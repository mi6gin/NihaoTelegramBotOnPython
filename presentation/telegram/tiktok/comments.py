"""TikTok comment card and translation handlers."""

import asyncio
from typing import Optional

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery
from aiogram_i18n import I18nContext
from deep_translator import GoogleTranslator

from database.models.user import User
from presentation.telegram.tiktok.keyboards import (
    get_tiktok_comment_card_keyboard,
)
from presentation.telegram.tiktok.shared import tiktok_service
from utils.logger import logger


router = Router(name="tiktok_comments")


async def render_comment_card(
    callback: CallbackQuery,
    short_id: str,
    index: int,
    is_edit: bool = False,
    translated_text: Optional[str] = None,
    target_lang: str = "ru",
    i18n: Optional[I18nContext] = None,
):
    """Render one comment and its optional translation."""
    comments = tiktok_service.get_comments(short_id)
    if not comments or index < 1 or index > len(comments):
        error = (
            i18n.get("tiktok-comment-not-found")
            if i18n
            else "⚠️ Комментарий не найден."
        )
        await callback.answer(error, show_alert=True)
        return

    comment = comments[index - 1]
    total = len(comments)
    likes = f"{comment['likes']:,}".replace(",", " ")

    if i18n:
        lines = [
            f"{i18n.get('tiktok-comment-header', index=index, total=total)}\n"
            "───────────────────\n"
            f"{i18n.get('tiktok-comment-author', author=comment['author'])}\n"
            f"{i18n.get('tiktok-comment-likes', likes=likes)}\n\n"
            f"💬 <i>«{comment['text']}»</i>"
        ]
        if translated_text:
            language = "русский" if target_lang == "ru" else "English"
            heading = i18n.get(
                "tiktok-comment-trans-header",
                lang=language,
            )
            lines.append(
                f"\n\n{heading}\n<i>«{translated_text}»</i>"
            )
    else:
        lines = [
            f"💬 <b>Комментарий [ {index} из {total} ]</b>\n"
            "───────────────────\n"
            f"👤 <b>Автор:</b> {comment['author']}\n"
            f"❤️ <b>Лайков:</b> {likes}\n\n"
            f"💬 <i>«{comment['text']}»</i>"
        ]
        if translated_text:
            language = (
                "русский"
                if target_lang == "ru"
                else "английский"
            )
            lines.append(
                f"\n\n🌐 <b>Перевод на {language}:</b>\n"
                f"<i>«{translated_text}»</i>"
            )

    text = "".join(lines)
    reply_markup = get_tiktok_comment_card_keyboard(
        short_id,
        index,
        total,
        is_translated=bool(translated_text),
        i18n=i18n,
    )
    if is_edit:
        try:
            await callback.message.edit_text(
                text=text,
                reply_markup=reply_markup,
            )
        except Exception:
            await callback.message.answer(
                text=text,
                reply_markup=reply_markup,
            )
    else:
        await callback.message.answer(
            text=text,
            reply_markup=reply_markup,
        )


@router.callback_query(F.data.startswith("tt_comm_"), StateFilter("*"))
async def start_tiktok_comments_card(
    callback: CallbackQuery,
    i18n: Optional[I18nContext] = None,
):
    """Load comments and show the first card."""
    short_id = callback.data.replace("tt_comm_", "")
    if not tiktok_service.resolve_post_url(short_id):
        error = (
            i18n.get("tiktok-comments-link-expired")
            if i18n
            else "⚠️ Ссылка на пост устарела или не найдена."
        )
        await callback.answer(error, show_alert=True)
        return

    loading = (
        i18n.get("tiktok-comments-loading")
        if i18n
        else "⏳ Загрузка комментариев..."
    )
    await callback.answer(loading)
    comments = await tiktok_service.load_comments(short_id)
    if not comments:
        error = (
            i18n.get("tiktok-comments-none")
            if i18n
            else "💬 К этому видео не найдено комментариев или они закрыты автором."
        )
        await callback.answer(error, show_alert=True)
        return

    await render_comment_card(
        callback,
        short_id,
        index=1,
        is_edit=False,
        i18n=i18n,
    )


@router.callback_query(F.data.startswith("tt_card_"), StateFilter("*"))
async def navigate_tiktok_comment_card(
    callback: CallbackQuery,
    i18n: Optional[I18nContext] = None,
):
    """Navigate between cached comment cards."""
    await callback.answer()
    parts = callback.data.split("_")
    await render_comment_card(
        callback,
        parts[2],
        index=int(parts[3]),
        is_edit=True,
        i18n=i18n,
    )


@router.callback_query(F.data.startswith("tt_tr_"), StateFilter("*"))
async def translate_tiktok_comment_card(
    callback: CallbackQuery,
    db_user: User,
    i18n: Optional[I18nContext] = None,
):
    """Translate the current comment to the user's language."""
    parts = callback.data.split("_")
    short_id = parts[2]
    index = int(parts[3])
    comments = tiktok_service.get_comments(short_id)
    if not comments or index < 1 or index > len(comments):
        error = (
            i18n.get("tiktok-comment-not-found")
            if i18n
            else "⚠️ Комментарий не найден."
        )
        await callback.answer(error, show_alert=True)
        return

    comment = comments[index - 1]
    target_lang = (
        db_user.language
        if db_user and db_user.language in {"ru", "en"}
        else "ru"
    )
    loading = (
        i18n.get("tiktok-translation-loading")
        if i18n
        else "⏳ Перевод с помощью Google Translate..."
    )
    await callback.answer(loading)
    try:
        translated = await asyncio.to_thread(
            GoogleTranslator(
                source="auto",
                target=target_lang,
            ).translate,
            comment["text"],
        )
    except Exception as error:
        logger.error(f"Translation error: {error}")
        message = (
            i18n.get("tiktok-translation-failed")
            if i18n
            else "⚠️ Не удалось выполнить перевод."
        )
        await callback.answer(message, show_alert=True)
        return

    await render_comment_card(
        callback,
        short_id=short_id,
        index=index,
        is_edit=True,
        translated_text=translated,
        target_lang=target_lang,
        i18n=i18n,
    )


@router.callback_query(F.data == "tiktok_comments_close", StateFilter("*"))
async def close_tiktok_comments(callback: CallbackQuery):
    """Close the comment card."""
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
