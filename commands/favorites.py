import math
import os
from typing import Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User as DBUser
from database.repository.favorite_repo import FavoriteTikTokRepository
from commands.tiktok.handlers import _post_urls_cache, register_post_url, format_user_caption, AnimatedStatus
from commands.tiktok.keyboards import (
    get_favorite_categories_keyboard,
    get_favorite_tiktoks_keyboard,
    get_tiktok_comments_button_keyboard,
)
from utils.tiktok_parser import TikTokParser
from utils.logger import logger

router = Router(name="favorites_router")


@router.callback_query(F.data == "user_favorites")
async def show_favorites_categories(callback: CallbackQuery, session: AsyncSession, i18n: I18nContext):
    """
    Показывает экран выбора категорий в разделе "Понравившиеся".
    """
    fav_count = await FavoriteTikTokRepository.count_user_favorites(session, callback.from_user.id)
    text = i18n.get("favorites-categories-title")
    reply_markup = get_favorite_categories_keyboard(fav_count, i18n)

    try:
        await callback.message.edit_text(text=text, reply_markup=reply_markup)
    except Exception:
        await callback.message.answer(text=text, reply_markup=reply_markup)
    await callback.answer()


@router.callback_query(F.data.startswith("fav_category_tiktok"))
@router.callback_query(F.data.startswith("fav_tt_page_"))
async def show_favorite_tiktoks(callback: CallbackQuery, session: AsyncSession, i18n: I18nContext):
    """
    Показывает список сохраненных видео TikTok пользователя с пагинацией.
    """
    page = 1
    if callback.data.startswith("fav_tt_page_"):
        try:
            page = int(callback.data.replace("fav_tt_page_", ""))
        except ValueError:
            page = 1

    limit = 5
    total = await FavoriteTikTokRepository.count_user_favorites(session, callback.from_user.id)

    if total == 0:
        text = i18n.get("favorites-tiktok-empty")
        reply_markup = get_favorite_categories_keyboard(0, i18n)
        try:
            await callback.message.edit_text(text=text, reply_markup=reply_markup)
        except Exception:
            await callback.message.answer(text=text, reply_markup=reply_markup)
        await callback.answer()
        return

    total_pages = math.ceil(total / limit)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * limit

    favorites = await FavoriteTikTokRepository.get_user_favorites(
        session=session,
        telegram_id=callback.from_user.id,
        limit=limit,
        offset=offset
    )

    text = i18n.get("favorites-tiktok-title", total=str(total))
    reply_markup = get_favorite_tiktoks_keyboard(favorites, page, total_pages, i18n)

    try:
        await callback.message.edit_text(text=text, reply_markup=reply_markup)
    except Exception:
        await callback.message.answer(text=text, reply_markup=reply_markup)
    await callback.answer()


@router.callback_query(F.data.startswith("fav_toggle_"))
async def toggle_favorite_video(callback: CallbackQuery, session: AsyncSession, i18n: I18nContext):
    """
    Переключает лайк / сохранение видео в Понравившиеся при клике по кнопке под видео.
    """
    short_id = callback.data.replace("fav_toggle_", "")
    url = _post_urls_cache.get(short_id)

    if not url:
        if short_id.startswith("v") and short_id[1:].isdigit():
            vid = short_id[1:]
            url = f"https://www.tiktok.com/@a/video/{vid}"
            _post_urls_cache[short_id] = url
        elif short_id.isdigit() and len(short_id) > 10:
            url = f"https://www.tiktok.com/@a/video/{short_id}"
            _post_urls_cache[short_id] = url

    if not url:
        await callback.answer("⚠️ Ссылка на видео не найдена.", show_alert=True)
        return

    video_id = TikTokParser.extract_video_id(url) or short_id
    title = _post_urls_cache.get(f"title_{short_id}", "TikTok Video")

    # Переключаем статус в базе данных
    is_added = await FavoriteTikTokRepository.toggle_favorite(
        session=session,
        telegram_id=callback.from_user.id,
        video_id=video_id,
        url=url,
        title=title
    )

    # Обновляем клавиатуру под сообщением
    reply_markup = get_tiktok_comments_button_keyboard(short_id, is_favorite=is_added, i18n=i18n)
    try:
        await callback.message.edit_reply_markup(reply_markup=reply_markup)
    except Exception:
        pass

    alert_text = i18n.get("favorites-added-alert") if is_added else i18n.get("favorites-removed-alert")
    await callback.answer(alert_text, show_alert=True)


@router.callback_query(F.data.startswith("fav_tt_play_"))
async def play_favorite_tiktok(callback: CallbackQuery, session: AsyncSession, db_user: DBUser, i18n: I18nContext):
    """
    При клике на сохраненное видео сразу скачивает и отправляет его медиафайл без промежуточных текстовых ссылок.
    """
    try:
        fav_id = int(callback.data.replace("fav_tt_play_", ""))
    except ValueError:
        await callback.answer("⚠️ Ошибка ID видео.", show_alert=True)
        return

    fav = await FavoriteTikTokRepository.get_by_id(session, fav_id)
    if not fav:
        await callback.answer("⚠️ Видео не найдено в вашей коллекции.", show_alert=True)
        return

    await callback.answer()
    tiktok_url = fav.url

    # 1. Отправляем статусный блок с локализацией и анимированным многоточием
    status_msg = await callback.message.answer(
        i18n.get("tiktok-downloading-status", link=tiktok_url, dots=".")
    )

    anim = AnimatedStatus(
        bot=callback.message.bot,
        chat_id=callback.message.chat.id,
        message_id=status_msg.message_id,
        base_key="tiktok-downloading-status",
        link=tiktok_url,
        i18n=i18n
    )
    anim.start()

    # 2. Скачиваем данные и информацию о посте
    info = await TikTokParser.get_post_info(tiktok_url)
    caption = format_user_caption(db_user, tiktok_url, i18n=i18n)

    resolved_url = info.get("resolved_url") or tiktok_url
    short_id = register_post_url(tiktok_url, resolved_url=resolved_url)
    reply_kb = get_tiktok_comments_button_keyboard(short_id, is_favorite=True, i18n=i18n)

    # 3. Если это фото-слайдшоу
    if info.get("type") == "photo" and info.get("images"):
        images = info["images"]
        media_group = [InputMediaPhoto(media=u, caption=caption if i == 0 else None) for i, u in enumerate(images[:10])]

        await anim.set_key("tiktok-uploading-status")
        try:
            await callback.message.bot.send_chat_action(chat_id=callback.message.chat.id, action="upload_photo")
        except Exception:
            pass

        try:
            await callback.message.answer_media_group(media=media_group)
            await callback.message.answer(i18n.get("btn-tiktok-comments"), reply_markup=reply_kb)
        except Exception as e:
            logger.error(f"Favorite play photo error: {e}")
            await callback.message.answer(i18n.get("tiktok-auto-photo-error", error=str(e)))
        finally:
            await anim.stop()
        return

    # 4. Если это обычное видео
    video_file = await TikTokParser.download_video(tiktok_url)

    await anim.set_key("tiktok-uploading-status")
    try:
        await callback.message.bot.send_chat_action(chat_id=callback.message.chat.id, action="upload_video")
    except Exception:
        pass

    if video_file and os.path.exists(video_file):
        try:
            video_input = FSInputFile(path=video_file)
            await callback.message.answer_video(video=video_input, caption=caption, reply_markup=reply_kb)
        except Exception as e:
            logger.error(f"Favorite play video error: {e}")
            await callback.message.answer(i18n.get("tiktok-auto-video-error", error=str(e)))
        finally:
            await anim.stop()
            if video_file and os.path.exists(video_file):
                try:
                    os.remove(video_file)
                except Exception:
                    pass
    else:
        await anim.stop()
        await callback.message.answer(i18n.get("tiktok-auto-video-error", error="Failed to download file"))
