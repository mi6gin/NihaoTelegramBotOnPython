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
        builder.button(text=i18n.get("btn-tiktok-refresh-stats"), callback_data="tiktok_account_menu")
        builder.button(text=i18n.get("btn-tiktok-edit"), callback_data="tiktok_bind_username")
        builder.button(text=i18n.get("btn-tiktok-unbind"), callback_data="tiktok_unbind_confirm")
        builder.button(text=i18n.get("btn-back-to-menu"), callback_data="back_to_menu")
        builder.adjust(1, 2, 1)
    else:
        builder.button(text=i18n.get("btn-tiktok-bind"), callback_data="tiktok_bind_username")
        builder.button(text=i18n.get("btn-back-to-menu"), callback_data="back_to_menu")
        builder.adjust(1, 1)
    return builder.as_markup()


def get_tiktok_unbind_confirm_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения отвязки аккаунта TikTok.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.get("btn-tiktok-unbind-confirm"), callback_data="tiktok_unbind_yes")
    builder.button(text=i18n.get("btn-cancel"), callback_data="tiktok_account_menu")
    builder.adjust(2)
    return builder.as_markup()


def get_tiktok_photo_mode_keyboard(i18n: I18nContext, total_slides: int = 0) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора режима скачивания слайдшоу для /Ptiktok.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.get("btn-tiktok-download-all", total=total_slides), callback_data="tiktok_photo_all")
    builder.button(text=i18n.get("btn-tiktok-select-slides"), callback_data="tiktok_photo_select_mode")
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
    action_builder.button(text=i18n.get("btn-tiktok-download-selected", count=count_selected), callback_data="tiktok_download_selected")
    action_builder.button(text=i18n.get("btn-tiktok-back-mode"), callback_data="tiktok_photo_back_mode")
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


def get_tiktok_comments_button_keyboard(
    short_id: str,
    is_favorite: bool = False,
    i18n: Optional[I18nContext] = None
) -> InlineKeyboardMarkup:
    """
    Инлайн-кнопки под отправленным видео/слайдшоу:
    [ ❤️ Сохранить ] / [ 💖 В Понравишихся ] и [ 💬 Комментарии ].
    """
    builder = InlineKeyboardBuilder()

    if is_favorite:
        fav_text = i18n.get("btn-fav-saved") if i18n else "💖"
    else:
        fav_text = i18n.get("btn-fav-save") if i18n else "❤️"

    builder.button(text=fav_text, callback_data=f"fav_toggle_{short_id}")

    btn_text = i18n.get("btn-tiktok-comments") if i18n else "💬 Комментарии"
    builder.button(text=btn_text, callback_data=f"tt_comm_{short_id}")

    builder.adjust(2)
    return builder.as_markup()


def get_favorite_categories_keyboard(fav_count: int, i18n: I18nContext) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора категорий в разделе "Понравившиеся".
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.get("btn-category-tiktok", count=str(fav_count)), callback_data="fav_category_tiktok")
    builder.button(text=i18n.get("btn-back-to-menu"), callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_favorite_tiktoks_keyboard(
    favorites: list,
    page: int,
    total_pages: int,
    i18n: I18nContext
) -> InlineKeyboardMarkup:
    """
    Инлайн-кнопки сохраненных видео TikTok с названиями ролей и пагинацией.
    """
    builder = InlineKeyboardBuilder()

    for fav in favorites:
        # Обрезаем название если слишком длинное
        title = fav.title.strip()
        if not title:
            title = "TikTok Video"
        display_title = title[:45] + "..." if len(title) > 48 else title
        builder.button(text=f"🎥 {display_title}", callback_data=f"fav_tt_play_{fav.id}")

    builder.adjust(1)

    # Пагинация
    if total_pages > 1:
        pag_builder = InlineKeyboardBuilder()
        if page > 1:
            pag_builder.button(text="◀️", callback_data=f"fav_tt_page_{page - 1}")
        pag_builder.button(text=f"{page}/{total_pages}", callback_data="noop")
        if page < total_pages:
            pag_builder.button(text="▶️", callback_data=f"fav_tt_page_{page + 1}")
        pag_builder.adjust(3 if (page > 1 and page < total_pages) else 2)
        builder.attach(pag_builder)

    back_builder = InlineKeyboardBuilder()
    back_builder.button(text=i18n.get("btn-back-to-menu"), callback_data="user_favorites")
    back_builder.adjust(1)
    builder.attach(back_builder)

    return builder.as_markup()


def get_tiktok_comment_card_keyboard(short_id: str, index: int, total: int, is_translated: bool = False, i18n: Optional[I18nContext] = None) -> InlineKeyboardMarkup:
    """
    Инлайн-кнопки карусели для пошагового просмотра карточек комментариев (◀️ Назад | 1/N | Вперед ▶️ + 🌐 Перевести).
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

    action_builder = InlineKeyboardBuilder()
    btn_trans = i18n.get("btn-tiktok-translate") if i18n else "🌐 Перевести"
    btn_hide = i18n.get("btn-tiktok-hide-comments") if i18n else "❌ Скрыть комментарии"

    if not is_translated:
        action_builder.button(text=btn_trans, callback_data=f"tt_tr_{short_id}_{index}")
    action_builder.button(text=btn_hide, callback_data="tiktok_comments_close")
    action_builder.adjust(1)

    builder.attach(action_builder)
    return builder.as_markup()



