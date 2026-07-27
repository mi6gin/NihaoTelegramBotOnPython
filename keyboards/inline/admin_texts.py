from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from aiogram_i18n import I18nContext


def get_admin_texts_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора динамического текста для редактирования.
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопки редактирования приветствия /dedinside на RU и EN
    builder.button(
        text="✏️ /dedinside (RU)",
        callback_data="admin_edit_text_dedinside_title_ru"
    )
    builder.button(
        text="✏️ /dedinside (EN)",
        callback_data="admin_edit_text_dedinside_title_en"
    )
    builder.button(
        text=i18n.get("btn-admin-panel"),
        callback_data="admin_panel_entry"
    )
    builder.adjust(2, 1)
    return builder.as_markup()
