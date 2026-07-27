from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram_i18n import I18nContext

from database.models.user import User
from keyboards.inline.user_menu import get_user_menu_keyboard
from filters.is_admin import IsAdmin
from filters.is_private import IsPrivate
from utils.logger import logger

router = Router(name="user_start")


@router.message(CommandStart(), IsPrivate())
async def cmd_start(message: Message, db_user: User, i18n: I18nContext):
    """
    Обработчик команды /start.
    Показывает главное меню пользователю. Регистрация происходит автоматически в middleware.
    """
    logger.info(f"User {message.from_user.id} triggered /start")
    
    is_admin_user = await IsAdmin()(message, db_user)
    await message.answer(
        i18n.get("welcome-text-start", name=db_user.first_name),
        reply_markup=get_user_menu_keyboard(i18n, is_admin=is_admin_user)
    )


@router.message(Command("help"), IsPrivate())
async def cmd_help(message: Message, db_user: User, i18n: I18nContext):
    """
    Обработчик команды /help.
    Показывает справочную информацию по доступным командам.
    """
    is_admin_user = await IsAdmin()(message, db_user)
    help_text = i18n.get("help-text")
    if is_admin_user:
        help_text += i18n.get("help-text-admin")

    await message.answer(help_text)


@router.message(Command("about"), IsPrivate())
async def cmd_about(message: Message, i18n: I18nContext):
    """
    Обработчик команды /about.
    Предоставляет описание проекта.
    """
    await message.answer(i18n.get("about-text"))


# --- Хендлеры возврата в меню ---

@router.callback_query(F.data == "back_to_menu", IsPrivate())
async def process_back_to_menu(callback: CallbackQuery, db_user: User, i18n: I18nContext, state: FSMContext):
    """
    Возврат в главное меню при нажатии inline-кнопки.
    Очищает любые активные состояния FSM при переходе.
    """
    await state.clear()
    await callback.answer()
    is_admin_user = await IsAdmin()(callback, db_user)
    await callback.message.edit_text(
        i18n.get("menu-title"),
        reply_markup=get_user_menu_keyboard(i18n, is_admin=is_admin_user)
    )
