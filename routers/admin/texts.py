from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram_i18n import I18nContext

from database.repository.bot_text_repo import BotTextRepository
from keyboards.inline.admin_texts import get_admin_texts_keyboard
from keyboards.inline.cancel import get_cancel_inline_keyboard
from states.admin_texts import AdminTextStates
from filters.is_private import IsPrivate
from filters.is_admin import IsAdmin
from utils.logger import logger

from utils.text_manager import text_manager

router = Router(name="admin_texts")


@router.callback_query(F.data == "admin_texts_manage", IsPrivate(), IsAdmin())
async def show_admin_texts_menu(callback: CallbackQuery, session: AsyncSession, i18n: I18nContext, state: FSMContext):
    """
    Показывает меню управления динамическими текстами бота.
    """
    await state.clear()
    await callback.answer()

    ru_text = text_manager.get_text("dedinside-title", i18n=type("MockI18n", (), {"locale": "ru", "get": lambda self, k: i18n.get(k, locale="ru")})())
    en_text = text_manager.get_text("dedinside-title", i18n=type("MockI18n", (), {"locale": "en", "get": lambda self, k: i18n.get(k, locale="en")})())

    menu_text = (
        "📝 <b>Управление текстами бота в СУБД (In-Memory RAM кэш)</b>\n\n"
        "Вы можете изменить приветственный текст команды /dedinside.\n\n"
        f"<b>Текущий текст RU:</b>\n<code>{ru_text}</code>\n\n"
        f"<b>Текущий текст EN:</b>\n<code>{en_text}</code>\n\n"
        "Выберите, какой язык отредактировать:"
    )

    await callback.message.edit_text(
        menu_text,
        reply_markup=get_admin_texts_keyboard(i18n)
    )


@router.callback_query(F.data.in_({"admin_edit_text_dedinside_title_ru", "admin_edit_text_dedinside_title_en"}), IsPrivate(), IsAdmin())
async def start_editing_text(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Запускает процесс ввода нового текста.
    """
    await callback.answer()
    
    lang = "ru" if callback.data.endswith("_ru") else "en"
    key = "dedinside-title"

    await state.set_state(AdminTextStates.waiting_for_text_content)
    await state.update_data(edit_key=key, edit_lang=lang)

    prompt_msg = await callback.message.edit_text(
        f"✍️ <b>Введите новый текст для /dedinside ({lang.upper()}):</b>\n\n"
        f"Отправьте текстовое сообщение или нажмите Отмена.",
        reply_markup=get_cancel_inline_keyboard(i18n, callback_data="admin_texts_manage")
    )
    await state.update_data(prompt_msg_id=prompt_msg.message_id)


@router.message(AdminTextStates.waiting_for_text_content, IsPrivate(), IsAdmin(), F.text)
async def process_new_text_input(message: Message, state: FSMContext, session: AsyncSession, i18n: I18nContext):
    """
    Сохраняет новый текст в СУБД, обновляет RAM кэш и возвращает в меню.
    """
    new_text = message.text.strip()
    data = await state.get_data()
    key = data.get("edit_key", "dedinside-title")
    lang = data.get("edit_lang", "ru")

    await text_manager.set_text(session, key, lang, new_text)
    logger.info(f"Admin {message.from_user.id} updated text '{key}' ({lang}) to: '{new_text}'")

    await state.clear()

    try:
        await message.delete()
    except Exception:
        pass

    ru_text = text_manager.get_text("dedinside-title", i18n=type("MockI18n", (), {"locale": "ru", "get": lambda self, k: i18n.get(k, locale="ru")})())
    en_text = text_manager.get_text("dedinside-title", i18n=type("MockI18n", (), {"locale": "en", "get": lambda self, k: i18n.get(k, locale="en")})())

    menu_text = (
        "✅ <b>Текст успешно сохранен в базе данных и кэше RAM!</b>\n\n"
        f"<b>Текущий текст RU:</b>\n<code>{ru_text}</code>\n\n"
        f"<b>Текущий текст EN:</b>\n<code>{en_text}</code>"
    )

    await message.answer(
        menu_text,
        reply_markup=get_admin_texts_keyboard(i18n)
    )
