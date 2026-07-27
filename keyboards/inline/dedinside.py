from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from aiogram_i18n import I18nContext


def get_dedinside_menu_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора количества повторений для /dedinside (5 или 10 раз + Отмена).
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=i18n.get("dedinside-btn-5"),
        callback_data="dedinside_count_5"
    )
    builder.button(
        text=i18n.get("dedinside-btn-10"),
        callback_data="dedinside_count_10"
    )
    builder.button(
        text=i18n.get("dedinside-btn-cancel"),
        callback_data="dedinside_cancel"
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def get_dedinside_cancel_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """
    Клавиатура с единственной кнопкой Отмена при ожидании ввода текста.
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=i18n.get("dedinside-btn-cancel"),
        callback_data="dedinside_cancel"
    )
    return builder.as_markup()
