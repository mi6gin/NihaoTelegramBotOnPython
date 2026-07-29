from typing import Optional
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from aiogram_i18n import I18nContext


def get_user_menu_keyboard(i18n: I18nContext, is_admin: bool = False, user_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """
    Возвращает главное меню пользователя с кнопками Профиля, Каталога, Понравившихся и Поддержки.
    Поддерживает привязку к user_id для защиты от кликов чужих пользователей в группах.
    """
    builder = InlineKeyboardBuilder()

    suffix = f":{user_id}" if user_id else ""
    
    # Добавляем основные кнопки
    builder.button(text=i18n.get("btn-profile"), callback_data=f"user_profile{suffix}")
    builder.button(text=i18n.get("btn-tiktok-account"), callback_data=f"tiktok_account_menu{suffix}")
    builder.button(text=i18n.get("btn-favorites"), callback_data=f"user_favorites{suffix}")
    builder.button(text=i18n.get("btn-catalog"), callback_data=f"user_catalog{suffix}")
    builder.button(text=i18n.get("btn-support"), callback_data=f"user_support{suffix}")
    
    # Условная кнопка для администратора
    if is_admin:
        builder.button(text=i18n.get("btn-admin"), callback_data=f"admin_panel_entry{suffix}")
        
    # Размещаем по 1 кнопке в ряд
    builder.adjust(1)
    
    return builder.as_markup()
