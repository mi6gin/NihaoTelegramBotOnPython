from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from aiogram_i18n import I18nContext


def get_admin_panel_keyboard(i18n: I18nContext, open_tickets_count: int = 0) -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру панели администратора.
    Включает разделы статистики, рассылки, управления пользователями, обращений и возврата в меню.
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text=i18n.get("btn-admin-stats"), callback_data="admin_stats")
    builder.button(text=i18n.get("btn-admin-mailing"), callback_data="admin_mailing")
    builder.button(text=i18n.get("btn-admin-users"), callback_data="admin_users_manage")
    builder.button(text=i18n.get("btn-admin-texts"), callback_data="admin_texts_manage")
    builder.button(text=i18n.get("btn-admin-tickets", count=str(open_tickets_count)), callback_data="admin_tickets_view_0")
    builder.button(text=i18n.get("btn-admin-logs"), callback_data="admin_get_logs")
    builder.button(text=i18n.get("btn-back-to-menu"), callback_data="back_to_menu")
    
    # По 2 кнопки в рядах
    builder.adjust(2, 2, 2, 1)
    
    return builder.as_markup()
