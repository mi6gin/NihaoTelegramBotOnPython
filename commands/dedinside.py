import asyncio
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext

from filters.is_private import IsPrivate
from utils.logger import logger
from utils.text_manager import text_manager

router = Router(name="user_dedinside")


class DedinsideStates(StatesGroup):
    """
    Состояния FSM только для команды /dedinside.
    """
    selecting_count = State()      # Выбор количества сообщений (5 или 10)
    waiting_for_message = State()  # Ожидание текстового сообщения от пользователя
    sending_spam = State()         # Процесс последовательной отправки и удаления сообщений


def get_dedinside_menu_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора количества повторений для /dedinside (5 или 10 раз + Отмена).
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.get("dedinside-btn-5"), callback_data="dedinside_count_5")
    builder.button(text=i18n.get("dedinside-btn-10"), callback_data="dedinside_count_10")
    builder.button(text=i18n.get("dedinside-btn-cancel"), callback_data="dedinside_cancel")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_dedinside_cancel_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """
    Клавиатура с единственной кнопкой Отмена при ожидании ввода текста.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.get("dedinside-btn-cancel"), callback_data="dedinside_cancel")
    return builder.as_markup()


def get_dedinside_stop_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой "🛑 Остановить рассылку" во время активного спама.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.get("dedinside-btn-stop"), callback_data="dedinside_stop")
    return builder.as_markup()


@router.message(Command("dedinside"), IsPrivate(), StateFilter("*"))
async def cmd_dedinside(message: Message, state: FSMContext, i18n: I18nContext):
    """
    Запуск команды /dedinside.
    Если у пользователя уже есть активное состояние (меню, ожидание текста или спам),
    повторный вызов блокируется сообщением.
    """
    current_state = await state.get_state()
    if current_state is not None:
        await message.answer(text_manager.get_text("dedinside-already-active", i18n))
        return

    title_text = text_manager.get_text("dedinside-title", i18n)

    menu_msg = await message.answer(
        title_text,
        reply_markup=get_dedinside_menu_keyboard(i18n)
    )

    await state.set_state(DedinsideStates.selecting_count)
    await state.update_data(menu_msg_id=menu_msg.message_id)


@router.callback_query(F.data == "dedinside_cancel", IsPrivate(), StateFilter("*"))
async def process_dedinside_cancel(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик отмены команды /dedinside.
    Удаляет сообщение-меню и подсказки, затем сбрасывает FSM состояние.
    """
    await callback.answer()

    data = await state.get_data()
    menu_msg_id = data.get("menu_msg_id")
    prompt_msg_id = data.get("prompt_msg_id")

    for msg_id in (prompt_msg_id, menu_msg_id):
        if msg_id:
            try:
                await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
            except Exception:
                pass

    try:
        await callback.message.delete()
    except Exception:
        pass

    await state.clear()


@router.callback_query(F.data == "dedinside_stop", DedinsideStates.sending_spam, IsPrivate())
async def process_dedinside_stop(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Обработчик экстренной остановки рассылки.
    """
    await callback.answer(i18n.get("dedinside-stopped-alert"), show_alert=True)
    await state.update_data(stopped=True)


@router.callback_query(F.data.in_({"dedinside_count_5", "dedinside_count_10"}), DedinsideStates.selecting_count, IsPrivate())
async def process_count_selection(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Обработка клика по кнопкам "5 раз" или "10 раз".
    Отправляет новое сообщение-подсказку с запросом текста и кнопкой "Отмена".
    """
    await callback.answer()

    count = 5 if callback.data == "dedinside_count_5" else 10

    prompt_msg = await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=i18n.get("dedinside-prompt-text", count=str(count)),
        reply_markup=get_dedinside_cancel_keyboard(i18n)
    )

    await state.set_state(DedinsideStates.waiting_for_message)
    await state.update_data(count=count, prompt_msg_id=prompt_msg.message_id)


@router.message(DedinsideStates.waiting_for_message, IsPrivate(), ~F.text)
async def process_non_text_message(message: Message, i18n: I18nContext):
    """
    Обработка отправки не-текстового сообщения (фото, стикер, файл, голос и т.д.).
    Бот игнорирует содержимое и просит отправить текст.
    """
    await message.answer(i18n.get("dedinside-warn-only-text"))


@router.message(DedinsideStates.waiting_for_message, IsPrivate(), F.text)
async def process_spam_text_message(message: Message, state: FSMContext, i18n: I18nContext):
    """
    Обработка текста для рассылки.
    Последовательно отправляет и сразу удаляет сообщение 5 или 10 раз.
    Сохраняет контрольное меню с кнопкой "🛑 Остановить рассылку".
    """
    data = await state.get_data()
    count = data.get("count", 5)
    menu_msg_id = data.get("menu_msg_id")
    prompt_msg_id = data.get("prompt_msg_id")

    await state.set_state(DedinsideStates.sending_spam)

    if prompt_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_msg_id)
        except Exception:
            pass

    try:
        await message.delete()
    except Exception:
        pass

    # Превращаем главное меню в контрольную панель активной рассылки с кнопкой "Остановить"
    status_msg = None
    if menu_msg_id:
        try:
            status_msg = await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text=i18n.get("dedinside-active-status", current=1, total=count),
                reply_markup=get_dedinside_stop_keyboard(i18n)
            )
        except Exception:
            pass

    if not status_msg:
        try:
            status_msg = await message.bot.send_message(
                chat_id=message.chat.id,
                text=i18n.get("dedinside-active-status", current=1, total=count),
                reply_markup=get_dedinside_stop_keyboard(i18n)
            )
        except Exception:
            pass

    spam_text = message.text
    chat_id = message.chat.id

    for i in range(1, count + 1):
        curr_data = await state.get_data()
        if curr_data.get("stopped"):
            break

        try:
            sent_msg = await message.bot.send_message(chat_id=chat_id, text=spam_text)
            await asyncio.sleep(0.8)
            await message.bot.delete_message(chat_id=chat_id, message_id=sent_msg.message_id)
        except Exception as e:
            logger.warning(f"Error sending dedinside spam message: {e}")

    final_menu_id = status_msg.message_id if status_msg else menu_msg_id
    if final_menu_id:
        try:
            await message.bot.delete_message(chat_id=chat_id, message_id=final_menu_id)
        except Exception:
            pass

    await state.clear()
