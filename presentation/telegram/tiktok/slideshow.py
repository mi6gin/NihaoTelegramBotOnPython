"""TikTok slideshow download and selection handlers."""

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from aiogram_i18n import I18nContext

from database.models.user import User
from infrastructure.tiktok import TikTokParser
from presentation.telegram.tiktok.keyboards import (
    get_tiktok_cancel_keyboard,
    get_tiktok_photo_mode_keyboard,
    get_tiktok_slides_grid_keyboard,
)
from presentation.telegram.tiktok.shared import format_user_caption
from presentation.telegram.tiktok.states import TikTokStates
from utils.logger import logger


router = Router(name="tiktok_slideshow")


@router.message(Command("ptiktok", "Ptiktok", ignore_case=True))
async def cmd_ptiktok(
    message: Message,
    state: FSMContext,
    i18n: I18nContext,
):
    """Start the slideshow-only TikTok flow."""
    await state.clear()
    await state.set_state(TikTokStates.waiting_for_photo_link)
    prompt_msg = await message.answer(
        i18n.get("tiktok-ptiktok-prompt-msg"),
        reply_markup=get_tiktok_cancel_keyboard(
            i18n,
            callback_data="tiktok_cancel",
        ),
    )
    await state.update_data(prompt_msg_id=prompt_msg.message_id)


@router.message(TikTokStates.waiting_for_photo_link, F.text)
async def process_photo_link_input(
    message: Message,
    state: FSMContext,
    i18n: I18nContext,
):
    """Load slideshow metadata and show its download modes."""
    tiktok_url = TikTokParser.extract_url_from_text(message.text)
    if not tiktok_url:
        await message.answer(i18n.get("tiktok-err-url-invalid"))
        return

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    if prompt_msg_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=prompt_msg_id,
            )
        except Exception:
            pass

    try:
        await message.bot.send_chat_action(
            chat_id=message.chat.id,
            action="upload_photo",
        )
    except Exception:
        pass

    info = await TikTokParser.get_post_info(tiktok_url)
    images = info.get("images", [])
    if not images:
        await message.answer(i18n.get("tiktok-err-no-slideshow"))
        await state.clear()
        return

    total_slides = len(images)
    await state.update_data(
        tiktok_url=tiktok_url,
        images=images,
        total_slides=total_slides,
        selected_slides=[],
    )
    await message.answer(
        text=i18n.get(
            "tiktok-slideshow-found-msg",
            total=total_slides,
        ),
        reply_markup=get_tiktok_photo_mode_keyboard(
            i18n,
            total_slides,
        ),
    )


@router.callback_query(F.data == "tiktok_photo_all")
async def download_all_slides(
    callback: CallbackQuery,
    state: FSMContext,
    db_user: User,
    i18n: I18nContext,
):
    """Send all available slides as a Telegram album."""
    await callback.answer()
    data = await state.get_data()
    images = data.get("images", [])
    if not images:
        await callback.message.answer(
            i18n.get("tiktok-err-slideshow-data")
        )
        await state.clear()
        return

    caption = format_user_caption(
        db_user,
        data.get("tiktok_url", ""),
        i18n=i18n,
    )
    media_group = [
        InputMediaPhoto(
            media=url,
            caption=caption if index == 0 else None,
        )
        for index, url in enumerate(images[:10])
    ]
    try:
        await callback.message.answer_media_group(media=media_group)
    except Exception as error:
        logger.error(f"Error sending media group: {error}")
        await callback.message.answer(
            i18n.get("tiktok-err-send-slides")
        )
    await state.clear()


@router.callback_query(F.data == "tiktok_photo_select_mode")
async def enter_slides_selection_mode(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nContext,
):
    """Enter interactive slide selection mode."""
    await callback.answer()
    data = await state.get_data()
    total_slides = data.get("total_slides", 0)
    selected_slides = set(data.get("selected_slides", []))
    await state.set_state(TikTokStates.selecting_slides)
    await _render_selection(
        callback,
        total_slides,
        selected_slides,
        i18n,
    )


async def _render_selection(
    callback: CallbackQuery,
    total_slides: int,
    selected_slides: set[int],
    i18n: I18nContext,
) -> None:
    selected = ", ".join(map(str, sorted(selected_slides)))
    await callback.message.edit_text(
        text=i18n.get(
            "tiktok-select-slides-prompt",
            selected=selected,
        ),
        reply_markup=get_tiktok_slides_grid_keyboard(
            total_slides,
            selected_slides,
            i18n,
        ),
    )


@router.callback_query(
    F.data.startswith("tiktok_toggle_slide_"),
    TikTokStates.selecting_slides,
)
async def toggle_slide_selection(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nContext,
):
    """Toggle one slide in the current selection."""
    await callback.answer()
    slide_num = int(
        callback.data.replace("tiktok_toggle_slide_", "")
    )
    data = await state.get_data()
    selected_slides = set(data.get("selected_slides", []))
    if slide_num in selected_slides:
        selected_slides.remove(slide_num)
    else:
        selected_slides.add(slide_num)
    await state.update_data(selected_slides=list(selected_slides))
    await _render_selection(
        callback,
        data.get("total_slides", 0),
        selected_slides,
        i18n,
    )


@router.callback_query(
    F.data == "tiktok_download_selected",
    TikTokStates.selecting_slides,
)
async def download_selected_slides(
    callback: CallbackQuery,
    state: FSMContext,
    db_user: User,
    i18n: I18nContext,
):
    """Send only the selected slides."""
    data = await state.get_data()
    images = data.get("images", [])
    selected_slides = sorted(set(data.get("selected_slides", [])))
    if not selected_slides:
        await callback.answer(
            i18n.get("tiktok-err-no-slides-selected"),
            show_alert=True,
        )
        return

    await callback.answer()
    caption = format_user_caption(
        db_user,
        data.get("tiktok_url", ""),
        i18n=i18n,
    )
    selected_urls = [
        images[index - 1]
        for index in selected_slides
        if 0 <= index - 1 < len(images)
    ]
    media_group = [
        InputMediaPhoto(
            media=url,
            caption=caption if index == 0 else None,
        )
        for index, url in enumerate(selected_urls[:10])
    ]
    try:
        await callback.message.answer_media_group(media=media_group)
    except Exception as error:
        logger.error(f"Error sending selected slides: {error}")
        await callback.message.answer(
            i18n.get("tiktok-err-send-slides")
        )
    await state.clear()


@router.callback_query(
    F.data == "tiktok_photo_back_mode",
    TikTokStates.selecting_slides,
)
async def back_to_photo_mode(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nContext,
):
    """Return from selection to slideshow mode selection."""
    await callback.answer()
    data = await state.get_data()
    total_slides = data.get("total_slides", 0)
    await callback.message.edit_text(
        text=i18n.get(
            "tiktok-slideshow-found-msg",
            total=total_slides,
        ),
        reply_markup=get_tiktok_photo_mode_keyboard(
            i18n,
            total_slides,
        ),
    )


@router.callback_query(F.data == "tiktok_cancel", StateFilter("*"))
async def tiktok_cancel(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Cancel any active TikTok flow."""
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await state.clear()
