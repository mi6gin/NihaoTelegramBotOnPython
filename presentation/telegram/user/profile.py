"""User profile Telegram handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram_i18n import I18nContext

from database.models.user import User
from keyboards.inline.profile import get_profile_keyboard, get_language_keyboard
from filters.is_private import IsPrivate

router = Router(name="user_profile")


def format_profile_text(user: User, i18n: I18nContext) -> str:
    """
    Форматирует текст профиля для отправки пользователю на основе выбранного языка.
    """
    username_str = f"@{user.username}" if user.username else i18n.get("profile-username-empty")
    reg_date = user.registered_at.strftime("%d.%m.%Y в %H:%M")
    
    theme_map = {
        "theme_classic": "catalog-classic-title",
        "theme_sakura": "catalog-sakura-title",
        "theme_cyberpunk": "catalog-cyberpunk-title"
    }
    theme_key = theme_map.get(user.selected_theme, "catalog-classic-title")
    theme_name = i18n.get(theme_key)
    
    return i18n.get(
        "profile-title",
        name=user.first_name,
        username=username_str,
        id=str(user.telegram_id),
        role=user.role,
        theme=theme_name,
        date=reg_date
    )


@router.callback_query(F.data.startswith("user_profile"))
async def show_profile(callback: CallbackQuery, db_user: User, i18n: I18nContext, state: FSMContext):
    """
    Показывает карточку профиля пользователя.
    Очищает любые активные состояния FSM при переходе.
    """
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(
        text=format_profile_text(db_user, i18n),
        reply_markup=get_profile_keyboard(i18n)
    )


@router.callback_query(F.data.startswith("change_language"))
async def show_language_selection(callback: CallbackQuery, i18n: I18nContext, state: FSMContext):
    """
    Показывает меню выбора языка.
    Очищает любые активные состояния FSM при переходе.
    """
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(
        text=i18n.get("lang-select-prompt"),
        reply_markup=get_language_keyboard()
    )


@router.callback_query(F.data.startswith("set_lang_"))
async def set_language(callback: CallbackQuery, db_user: User, i18n: I18nContext, state: FSMContext):
    """
    Сохраняет выбранный пользователем язык и возвращает в профиль.
    Очищает любые активные состояния FSM при переходе.
    """
    await state.clear()
    await callback.answer()
    lang = callback.data.split("_")[-1]
    if lang in ("ru", "en"):
        await i18n.set_locale(lang)
        
    await callback.message.edit_text(
        text=format_profile_text(db_user, i18n),
        reply_markup=get_profile_keyboard(i18n)
    )
