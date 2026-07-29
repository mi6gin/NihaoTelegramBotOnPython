import os
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, InputMediaPhoto, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram_i18n import I18nContext

from database.models.user import User
from database.repository.favorite_repo import FavoriteTikTokRepository
from infrastructure.tiktok import TikTokParser
from presentation.telegram.animated_status import AnimatedStatus
from utils.logger import logger

from presentation.telegram.tiktok.account import (
    process_username_input,
    router as account_router,
    show_tiktok_account_menu,
    start_bind_username,
    tiktok_unbind_confirm,
    tiktok_unbind_yes,
)
from presentation.telegram.tiktok.audio import (
    cmd_mtiktok,
    process_audio_link_input,
    router as audio_router,
)
from presentation.telegram.tiktok.comments import (
    close_tiktok_comments,
    navigate_tiktok_comment_card,
    render_comment_card,
    router as comments_router,
    start_tiktok_comments_card,
    translate_tiktok_comment_card,
)
from presentation.telegram.tiktok.shared import (
    _comments_cache,
    _post_urls_cache,
    format_user_caption,
    register_post_url,
    tiktok_service,
)
from presentation.telegram.tiktok.slideshow import (
    back_to_photo_mode,
    cmd_ptiktok,
    download_all_slides,
    download_selected_slides,
    enter_slides_selection_mode,
    process_photo_link_input,
    router as slideshow_router,
    tiktok_cancel,
    toggle_slide_selection,
)
from presentation.telegram.tiktok.keyboards import (
    get_tiktok_comments_button_keyboard,
)

router = Router(name="tiktok_main")
feed_router = Router(name="tiktok_feed")


# =====================================================================
# 📌 ПУНКТ 2: АВТОПЕРЕХВАТ ССЫЛОК TIKTOK В ЧАТЕ (Фильтр сообщений)
# =====================================================================

@feed_router.message(StateFilter(None), F.text)
async def auto_download_tiktok_link(message: Message, db_user: User, session: AsyncSession, i18n: I18nContext):
    """
    Автоматически распознает ссылки на TikTok в тексте сообщения и отправляет видео/слайдшоу.
    Удаляет сообщение пользователя с ссылкой, анимирует «Скачиваю...» -> «Отправляю...»,
    затем отправляет медиа и удаляет статусное сообщение.
    """
    tiktok_url = TikTokParser.extract_url_from_text(message.text)
    if not tiktok_url:
        return

    logger.info(f"User {db_user.telegram_id} sent TikTok link: {tiktok_url}")

    # 1. Удаляем исходное сообщение пользователя с ссылкой
    try:
        await message.delete()
    except Exception:
        pass

    # 2. Отправляем статусное сообщение «Скачиваю [ссылка]...» и запускаем анимацию точек
    status_msg = await message.answer(
        i18n.get("tiktok-downloading-status", link=tiktok_url, dots="."),
        disable_web_page_preview=True
    )
    anim = AnimatedStatus(
        bot=message.bot,
        chat_id=message.chat.id,
        message_id=status_msg.message_id,
        base_key="tiktok-downloading-status",
        link=tiktok_url,
        i18n=i18n
    )
    anim.start()

    # 3. Скачиваем данные и информацию о посте
    post = await tiktok_service.get_post(tiktok_url)
    caption = format_user_caption(db_user, tiktok_url, i18n=i18n)

    resolved_url = post.resolved_url
    short_id = register_post_url(tiktok_url, resolved_url=resolved_url)
    tiktok_service.remember_post_metadata(short_id, title=post.title)

    video_id = TikTokParser.extract_video_id(tiktok_url) or TikTokParser.extract_video_id(resolved_url) or short_id
    is_fav = await FavoriteTikTokRepository.is_favorite(session, db_user.telegram_id, video_id)

    reply_kb = get_tiktok_comments_button_keyboard(short_id, is_favorite=is_fav, i18n=i18n)

    # 4. Если это фото-слайдшоу
    if post.is_slideshow:
        images = post.images
        media_group = [InputMediaPhoto(media=url, caption=caption if i == 0 else None) for i, url in enumerate(images[:10])]

        # Меняем статус на «Отправляю [ссылка]...» и запускаем анимацию отправки бота
        await anim.set_key("tiktok-uploading-status")
        try:
            await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
        except Exception:
            pass

        try:
            await message.answer_media_group(media=media_group)
            await message.answer(i18n.get("btn-tiktok-comments"), reply_markup=reply_kb)
        except Exception as e:
            logger.error(f"Auto-download photo error: {e}")
            await message.answer(i18n.get("tiktok-auto-photo-error", error=str(e)))
        finally:
            await anim.stop()
        return

    # 5. Если это обычное видео
    video_file = await TikTokParser.download_video(tiktok_url)

    # Меняем статус на «Отправляю [ссылка]...» и запускаем анимацию отправки бота
    await anim.set_key("tiktok-uploading-status")
    try:
        await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_video")
    except Exception:
        pass

    if video_file and os.path.exists(video_file):
        try:
            video_input = FSInputFile(path=video_file)
            sent_msg = await message.answer_video(video=video_input, caption=caption, reply_markup=reply_kb)
            if sent_msg and sent_msg.video:
                tiktok_service.remember_post_metadata(
                    short_id,
                    file_id=sent_msg.video.file_id,
                )
        except Exception as e:
            logger.error(f"Auto-download video error: {e}")
            await message.answer(i18n.get("tiktok-auto-video-error", error=str(e)))
        finally:
            await anim.stop()
            if video_file and os.path.exists(video_file):
                try:
                    os.remove(video_file)
                except Exception:
                    pass
    else:
        await anim.stop()
        await message.answer(i18n.get("tiktok-auto-video-failed"))


router.include_routers(
    account_router,
    audio_router,
    slideshow_router,
    feed_router,
    comments_router,
)
