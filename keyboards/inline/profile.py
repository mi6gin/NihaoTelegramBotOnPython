from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from aiogram_i18n import I18nContext


def get_profile_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для страницы профиля со сменой языка, перехода к стилям и возвратом в меню.
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🌐 Language / Язык", callback_data="change_language")
    builder.button(text=i18n.get("btn-profile-change-theme"), callback_data="user_catalog")
    builder.button(text=i18n.get("btn-back-to-menu"), callback_data="back_to_menu")
    
    builder.adjust(1)
    
    return builder.as_markup()


def get_language_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру со списком доступных языков.
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🇷🇺 Русский", callback_data="set_lang_ru")
    builder.button(text="🇬🇧 English", callback_data="set_lang_en")
    builder.button(text="🔙 Назад / Back", callback_data="user_profile")
    
    builder.adjust(2, 1)
    
    return builder.as_markup()
