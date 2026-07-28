from typing import Optional, Set
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from aiogram_i18n import I18nContext


def get_tiktok_account_menu_keyboard(username: Optional[str], i18n: I18nContext) -> InlineKeyboardMarkup:
    """
    Клавиатура экрана 1.1 "Аккаунт TikTok".
    """
    builder = InlineKeyboardBuilder()
    if username:
        builder.button(text="✏️ Изменить аккаунт", callback_data="tiktok_bind_username")
        builder.button(text="🗑️ Отвязать аккаунт", callback_data="tiktok_unbind_confirm")
        builder.button(text=i18n.get("btn-back-to-menu"), callback_data="back_to_menu")
        builder.adjust(2, 1)
    else:
        builder.button(text="➕ Привязать аккаунт", callback_data="tiktok_bind_username")
        builder.button(text=i18n.get("btn-back-to-menu"), callback_data="back_to_menu")
        builder.adjust(1, 1)
    return builder.as_markup()


def get_tiktok_unbind_confirm_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения отвязки аккаунта TikTok.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, отвязать", callback_data="tiktok_unbind_yes")
    builder.button(text=i18n.get("btn-cancel"), callback_data="tiktok_account_menu")
    builder.adjust(2)
    return builder.as_markup()


def get_tiktok_photo_mode_keyboard(i18n: I18nContext, total_slides: int = 0) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора режима скачивания слайдшоу для /Ptiktok.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=f"📥 Скачать все ({total_slides})", callback_data="tiktok_photo_all")
    builder.button(text="🔢 Выбрать конкретные слайды", callback_data="tiktok_photo_select_mode")
    builder.button(text=i18n.get("btn-cancel"), callback_data="tiktok_cancel")
    builder.adjust(1)
    return builder.as_markup()


def get_tiktok_slides_grid_keyboard(total_slides: int, selected_slides: Set[int], i18n: I18nContext) -> InlineKeyboardMarkup:
    """
    Интерактивная сетка номеров слайдов с галочками [ ✅ 1 ].
    """
    builder = InlineKeyboardBuilder()

    # Сетка кнопок с цифрами
    for i in range(1, total_slides + 1):
        if i in selected_slides:
            builder.button(text=f"✅ {i}", callback_data=f"tiktok_toggle_slide_{i}")
        else:
            builder.button(text=f"{i}", callback_data=f"tiktok_toggle_slide_{i}")

    # По 5 цифр в ряду
    builder.adjust(5)

    # Кнопки действий под сеткой
    count_selected = len(selected_slides)
    action_builder = InlineKeyboardBuilder()
    action_builder.button(text=f"📥 Скачать выбранное ({count_selected})", callback_data="tiktok_download_selected")
    action_builder.button(text="🔙 Назад в выбор режима", callback_data="tiktok_photo_back_mode")
    action_builder.button(text=i18n.get("btn-cancel"), callback_data="tiktok_cancel")
    action_builder.adjust(1)

    builder.attach(action_builder)
    return builder.as_markup()


def get_tiktok_cancel_keyboard(i18n: I18nContext, callback_data: str = "tiktok_cancel") -> InlineKeyboardMarkup:
    """
    Клавиатура с единственной кнопкой Отмена.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.get("btn-cancel"), callback_data=callback_data)
    return builder.as_markup()


def get_tiktok_comments_button_keyboard(short_id: str) -> InlineKeyboardMarkup:
    """
    Инлайн-кнопка "💬 Комментарии" под отправленным видео/слайдшоу.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Комментарии", callback_data=f"tt_comm_{short_id}")
    return builder.as_markup()


def get_tiktok_comment_card_keyboard(short_id: str, index: int, total: int) -> InlineKeyboardMarkup:
    """
    Инлайн-кнопки карусели для пошагового просмотра карточек комментариев (◀️ Назад | 1/N | Вперед ▶️).
    """
    builder = InlineKeyboardBuilder()
    row_count = 0

    if index > 1:
        builder.button(text="◀️ Назад", callback_data=f"tt_card_{short_id}_{index - 1}")
        row_count += 1

    builder.button(text=f"{index} / {total}", callback_data="noop")
    row_count += 1

    if index < total:
        builder.button(text="Вперед ▶️", callback_data=f"tt_card_{short_id}_{index + 1}")
        row_count += 1

    builder.adjust(row_count)

    close_builder = InlineKeyboardBuilder()
    close_builder.button(text="❌ Скрыть комментарии", callback_data="tiktok_comments_close")
    close_builder.adjust(1)

    builder.attach(close_builder)
    return builder.as_markup()



