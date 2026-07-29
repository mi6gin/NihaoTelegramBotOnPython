"""TikTok audio download handlers."""

import os

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message
from aiogram_i18n import I18nContext

from database.models.user import User
from infrastructure.tiktok import TikTokParser
from presentation.telegram.tiktok.keyboards import get_tiktok_cancel_keyboard
from presentation.telegram.tiktok.shared import format_user_caption
from presentation.telegram.tiktok.states import TikTokStates
from utils.logger import logger


router = Router(name="tiktok_audio")


def _remove_file(path: str | None) -> None:
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


@router.message(Command("mtiktok", "Mtiktok", ignore_case=True))
async def cmd_mtiktok(
    message: Message,
    state: FSMContext,
    i18n: I18nContext,
):
    """Start the audio-only TikTok flow."""
    await state.clear()
    await state.set_state(TikTokStates.waiting_for_audio_link)
    prompt_msg = await message.answer(
        i18n.get("tiktok-mtiktok-prompt-msg"),
        reply_markup=get_tiktok_cancel_keyboard(
            i18n,
            callback_data="tiktok_cancel",
        ),
    )
    await state.update_data(prompt_msg_id=prompt_msg.message_id)


@router.message(TikTokStates.waiting_for_audio_link, F.text)
async def process_audio_link_input(
    message: Message,
    state: FSMContext,
    db_user: User,
    i18n: I18nContext,
):
    """Download and send an audio track from a TikTok URL."""
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
            action="upload_voice",
        )
    except Exception:
        pass

    info = await TikTokParser.get_post_info(tiktok_url)
    audio_file = await TikTokParser.download_audio(tiktok_url)
    if not audio_file or not os.path.exists(audio_file):
        await message.answer(i18n.get("tiktok-err-audio-failed"))
        await state.clear()
        return

    raw_title = (
        info.get("title")
        or info.get("music_title")
        or "TikTok Track"
    )
    track_title = (
        raw_title[:57] + "..."
        if len(raw_title) > 60
        else raw_title
    )
    performer = (
        info.get("author")
        or info.get("music_author")
        or "TikTok"
    )
    cover_url = info.get("cover")
    cover_file = (
        await TikTokParser.download_thumbnail(cover_url)
        if cover_url
        else None
    )

    try:
        audio_kwargs = {
            "audio": FSInputFile(path=audio_file),
            "caption": format_user_caption(
                db_user,
                tiktok_url,
                i18n=i18n,
            ),
            "title": track_title,
            "performer": performer,
        }
        if cover_file and os.path.exists(cover_file):
            audio_kwargs["thumbnail"] = FSInputFile(path=cover_file)
        await message.answer_audio(**audio_kwargs)
    except Exception as error:
        logger.error(f"Error sending audio file: {error}")
        await message.answer(i18n.get("tiktok-err-audio-send-failed"))
    finally:
        _remove_file(audio_file)
        _remove_file(cover_file)

    await state.clear()
