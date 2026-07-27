from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from aiogram_i18n import I18nContext


def get_user_menu_keyboard(i18n: I18nContext, is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    Возвращает главное меню пользователя с кнопками Профиля, Каталога и Поддержки.
    Если пользователь является администратором, добавляет кнопку 'Админ-панель'.
    """
    builder = InlineKeyboardBuilder()
    
    # Добавляем основные кнопки
    builder.button(text=i18n.get("btn-profile"), callback_data="user_profile")
    builder.button(text="📱 Аккаунт TikTok", callback_data="tiktok_account_menu")
    builder.button(text=i18n.get("btn-catalog"), callback_data="user_catalog")
    builder.button(text=i18n.get("btn-support"), callback_data="user_support")
    
    # Условная кнопка для администратора
    if is_admin:
        builder.button(text=i18n.get("btn-admin"), callback_data="admin_panel_entry")
        
    # Размещаем по 1 кнопке в ряд
    builder.adjust(1)
    
    return builder.as_markup()
