import os
import asyncio
from typing import Optional, List, Dict, Any
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram_i18n import I18nContext

from database.models.user import User
from database.repository.user_repo import UserRepository
from filters.is_private import IsPrivate
from utils.logger import logger
from utils.tiktok_parser import TikTokParser

from .states import TikTokStates
from .keyboards import (
    get_tiktok_account_menu_keyboard,
    get_tiktok_unbind_confirm_keyboard,
    get_tiktok_photo_mode_keyboard,
    get_tiktok_slides_grid_keyboard,
    get_tiktok_cancel_keyboard,
    get_tiktok_comments_button_keyboard,
)

router = Router(name="tiktok_main")

# Кэш кратких идентификаторов постов для инлайн-кнопок комментариев
_post_urls_cache = {}


def register_post_url(url: str) -> str:
    """
    Генерирует короткий ключ для URL поста и сохраняет в кэше.
    """
    short_id = str(abs(hash(url)) % 10000000)
    _post_urls_cache[short_id] = url
    return short_id


def format_user_caption(user: User, url: str) -> str:
    """
    Форматирует обязательную подпись к отправляемому медиафайлу:
    <b>@username</b> | <a href="...">&lt;TikTok&gt;</a>
    """
    name_str = f"@{user.username}" if user.username else user.first_name
    return f"<b>{name_str}</b> | <a href=\"{url}\">&lt;TikTok&gt;</a>"


# =====================================================================
# 📌 ПУНКТ 1: АККАУНТ TIKTOK (Навигация по меню)
# =====================================================================

@router.callback_query(F.data == "tiktok_account_menu")
async def show_tiktok_account_menu(callback: CallbackQuery, db_user: User, i18n: I18nContext, state: FSMContext):
    """
    Экран 1.1: Главное окно раздела "Аккаунт TikTok" со статистикой профиля.
    """
    await state.clear()
    await callback.answer()

    if db_user.tiktok_username:
        stats = await TikTokParser.fetch_user_info(db_user.tiktok_username)
        if stats:
            followers_fmt = f"{stats['followers']:,}".replace(",", " ")
            likes_fmt = f"{stats['likes']:,}".replace(",", " ")
            videos_fmt = f"{stats['videos']:,}".replace(",", " ")
            bio_text = stats['bio'] if stats['bio'] else "—"

            text = i18n.get(
                "tiktok-account-stats-title",
                username=stats['username'],
                nickname=stats['nickname'],
                followers=followers_fmt,
                likes=likes_fmt,
                videos=videos_fmt,
                bio=bio_text
            )
        else:
            text = i18n.get("tiktok-account-active-text", username=db_user.tiktok_username)
    else:
        text = i18n.get("tiktok-account-unlinked-text")

    await callback.message.edit_text(
        text=text,
        reply_markup=get_tiktok_account_menu_keyboard(db_user.tiktok_username, i18n)
    )


@router.callback_query(F.data == "tiktok_bind_username")
async def start_bind_username(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Экран 1.2: Запрос ввода юзернейма TikTok.
    """
    await callback.answer()
    await state.set_state(TikTokStates.waiting_for_username)

    prompt_msg = await callback.message.edit_text(
        i18n.get("tiktok-bind-prompt-msg"),
        reply_markup=get_tiktok_cancel_keyboard(i18n, callback_data="tiktok_account_menu")
    )
    await state.update_data(prompt_msg_id=prompt_msg.message_id)


@router.message(TikTokStates.waiting_for_username, F.text)
async def process_username_input(message: Message, state: FSMContext, session: AsyncSession, db_user: User, i18n: I18nContext):
    """
    Обработка введенного юзернейма TikTok и сохранение в БД.
    """
    raw_username = message.text.strip().lstrip("@")
    if not raw_username or len(raw_username) < 2 or len(raw_username) > 30:
        await message.answer(i18n.get("tiktok-err-invalid-username"))
        return

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    if prompt_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_msg_id)
        except Exception:
            pass

    try:
        await message.delete()
    except Exception:
        pass

    # Сохраняем в СУБД
    updated_user = await UserRepository.set_tiktok_username(session, db_user.telegram_id, raw_username)
    await state.clear()

    # Показываем обновившееся меню
    text = i18n.get("tiktok-bind-success-msg", username=raw_username)
    await message.answer(
        text=text,
        reply_markup=get_tiktok_account_menu_keyboard(raw_username, i18n)
    )


@router.callback_query(F.data == "tiktok_unbind_confirm")
async def tiktok_unbind_confirm(callback: CallbackQuery, db_user: User, i18n: I18nContext):
    """
    Экран 1.3: Подтверждение отвязки аккаунта.
    """
    await callback.answer()
    await callback.message.edit_text(
        i18n.get("tiktok-unbind-confirm-msg", username=db_user.tiktok_username),
        reply_markup=get_tiktok_unbind_confirm_keyboard(i18n)
    )


@router.callback_query(F.data == "tiktok_unbind_yes")
async def tiktok_unbind_yes(callback: CallbackQuery, session: AsyncSession, db_user: User, i18n: I18nContext):
    """
    Отвязывает аккаунт в СУБД и возвращает в меню.
    """
    await callback.answer(i18n.get("tiktok-unbind-alert"), show_alert=True)
    await UserRepository.set_tiktok_username(session, db_user.telegram_id, None)
    
    text = i18n.get("tiktok-account-unlinked-text")
    await callback.message.edit_text(
        text=text,
        reply_markup=get_tiktok_account_menu_keyboard(None, i18n)
    )


# =====================================================================
# 📌 ПУНКТ 3: МИКРО-МЕНЮ /Mtiktok (Только звук MP3)
# =====================================================================

@router.message(Command("mtiktok", "Mtiktok", ignore_case=True))
async def cmd_mtiktok(message: Message, state: FSMContext, i18n: I18nContext):
    """
    Старт микро-меню /mtiktok (Скачивание только аудио).
    """
    await state.clear()
    await state.set_state(TikTokStates.waiting_for_audio_link)

    prompt_msg = await message.answer(
        i18n.get("tiktok-mtiktok-prompt-msg"),
        reply_markup=get_tiktok_cancel_keyboard(i18n, callback_data="tiktok_cancel")
    )
    await state.update_data(prompt_msg_id=prompt_msg.message_id)


@router.message(TikTokStates.waiting_for_audio_link, F.text)
async def process_audio_link_input(message: Message, state: FSMContext, db_user: User, i18n: I18nContext):
    """
    Обработка ссылки для получения аудио MP3.
    """
    tiktok_url = TikTokParser.extract_url_from_text(message.text)
    if not tiktok_url:
        await message.answer(i18n.get("tiktok-err-url-invalid"))
        return

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    if prompt_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_msg_id)
        except Exception:
            pass

    try:
        await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_voice")
    except Exception:
        pass
    info = await TikTokParser.get_post_info(tiktok_url)
    audio_file = await TikTokParser.download_audio(tiktok_url)

    if not audio_file or not os.path.exists(audio_file):
        await message.answer(i18n.get("tiktok-err-audio-failed"))
        await state.clear()
        return

    # Заголовок трека (описание видео или наименование музыки)
    raw_title = info.get("title") or info.get("music_title") or "TikTok Track"
    track_title = raw_title[:57] + "..." if len(raw_title) > 60 else raw_title

    # Исполнитель (автор поста или музыки)
    performer = info.get("author") or info.get("music_author") or "TikTok"

    # Скачиваем обложку если доступна
    cover_url = info.get("cover")
    cover_file = await TikTokParser.download_thumbnail(cover_url) if cover_url else None

    caption = format_user_caption(db_user, tiktok_url)
    try:
        audio_kwargs = {
            "audio": FSInputFile(path=audio_file),
            "caption": caption,
            "title": track_title,
            "performer": performer
        }
        if cover_file and os.path.exists(cover_file):
            audio_kwargs["thumbnail"] = FSInputFile(path=cover_file)

        await message.answer_audio(**audio_kwargs)
    except Exception as e:
        logger.error(f"Error sending audio file: {e}")
        await message.answer(i18n.get("tiktok-err-audio-send-failed"))
    finally:
        if audio_file and os.path.exists(audio_file):
            try:
                os.remove(audio_file)
            except Exception:
                pass
        if cover_file and os.path.exists(cover_file):
            try:
                os.remove(cover_file)
            except Exception:
                pass

    await state.clear()


# =====================================================================
# 📌 ПУНКТ 4: МИКРО-МЕНЮ /Ptiktok (Слайдшоу / Карусели картинок)
# =====================================================================

@router.message(Command("ptiktok", "Ptiktok", ignore_case=True))
async def cmd_ptiktok(message: Message, state: FSMContext, i18n: I18nContext):
    """
    Старт микро-меню /Ptiktok (Скачивание слайдшоу).
    """
    await state.clear()
    await state.set_state(TikTokStates.waiting_for_photo_link)

    prompt_msg = await message.answer(
        i18n.get("tiktok-ptiktok-prompt-msg"),
        reply_markup=get_tiktok_cancel_keyboard(i18n, callback_data="tiktok_cancel")
    )
    await state.update_data(prompt_msg_id=prompt_msg.message_id)


@router.message(TikTokStates.waiting_for_photo_link, F.text)
async def process_photo_link_input(message: Message, state: FSMContext, i18n: I18nContext):
    """
    Обработка ссылки на слайдшоу и переход в окно выбора режима (Экран 4.2).
    """
    tiktok_url = TikTokParser.extract_url_from_text(message.text)
    if not tiktok_url:
        await message.answer(i18n.get("tiktok-err-url-invalid"))
        return

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    if prompt_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_msg_id)
        except Exception:
            pass

    try:
        await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
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
        selected_slides=list()
    )

    text = i18n.get("tiktok-slideshow-found-msg", total=total_slides)
    await message.answer(
        text=text,
        reply_markup=get_tiktok_photo_mode_keyboard(i18n, total_slides)
    )


@router.callback_query(F.data == "tiktok_photo_all")
async def download_all_slides(callback: CallbackQuery, state: FSMContext, db_user: User, i18n: I18nContext):
    """
    Скачивание всех картинок из слайдшоу альбомом.
    """
    await callback.answer()
    data = await state.get_data()
    images = data.get("images", [])
    tiktok_url = data.get("tiktok_url", "")

    if not images:
        await callback.message.answer(i18n.get("tiktok-err-slideshow-data"))
        await state.clear()
        return

    caption = format_user_caption(db_user, tiktok_url)
    media_group = [InputMediaPhoto(media=url, caption=caption if i == 0 else None) for i, url in enumerate(images[:10])]

    try:
        await callback.message.answer_media_group(media=media_group)
    except Exception as e:
        logger.error(f"Error sending media group: {e}")
        await callback.message.answer(i18n.get("tiktok-err-send-slides"))

    await state.clear()


@router.callback_query(F.data == "tiktok_photo_select_mode")
async def enter_slides_selection_mode(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Переход в интерактивную сетку выбора конкретных слайдов (Экран 4.3).
    """
    await callback.answer()
    data = await state.get_data()
    total_slides = data.get("total_slides", 0)
    selected_slides = set(data.get("selected_slides", []))

    await state.set_state(TikTokStates.selecting_slides)

    selected_str = ", ".join(map(str, sorted(selected_slides)))
    text = i18n.get("tiktok-select-slides-prompt", selected=selected_str)

    await callback.message.edit_text(
        text=text,
        reply_markup=get_tiktok_slides_grid_keyboard(total_slides, selected_slides, i18n)
    )


@router.callback_query(F.data.startswith("tiktok_toggle_slide_"), TikTokStates.selecting_slides)
async def toggle_slide_selection(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Переключает галочку на выбранном номере слайда.
    """
    await callback.answer()
    slide_num = int(callback.data.replace("tiktok_toggle_slide_", ""))

    data = await state.get_data()
    total_slides = data.get("total_slides", 0)
    selected_slides = set(data.get("selected_slides", []))

    if slide_num in selected_slides:
        selected_slides.remove(slide_num)
    else:
        selected_slides.add(slide_num)

    await state.update_data(selected_slides=list(selected_slides))

    selected_str = ", ".join(map(str, sorted(selected_slides)))
    text = i18n.get("tiktok-select-slides-prompt", selected=selected_str)

    await callback.message.edit_text(
        text=text,
        reply_markup=get_tiktok_slides_grid_keyboard(total_slides, selected_slides, i18n)
    )


@router.callback_query(F.data == "tiktok_download_selected", TikTokStates.selecting_slides)
async def download_selected_slides(callback: CallbackQuery, state: FSMContext, db_user: User, i18n: I18nContext):
    """
    Скачивание только отфильтрованных слайдов с проверкой на пустой выбор.
    """
    data = await state.get_data()
    images = data.get("images", [])
    tiktok_url = data.get("tiktok_url", "")
    selected_slides = sorted(list(set(data.get("selected_slides", []))))

    if not selected_slides:
        await callback.answer(i18n.get("tiktok-err-no-slides-selected"), show_alert=True)
        return

    await callback.answer()
    caption = format_user_caption(db_user, tiktok_url)
    
    selected_image_urls = [images[i - 1] for i in selected_slides if 0 <= i - 1 < len(images)]
    media_group = [InputMediaPhoto(media=url, caption=caption if idx == 0 else None) for idx, url in enumerate(selected_image_urls[:10])]

    try:
        await callback.message.answer_media_group(media=media_group)
    except Exception as e:
        logger.error(f"Error sending selected slides: {e}")
        await callback.message.answer(i18n.get("tiktok-err-send-slides"))

    await state.clear()


@router.callback_query(F.data == "tiktok_photo_back_mode", TikTokStates.selecting_slides)
async def back_to_photo_mode(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Возврат из сетки слайдов на выбор режима (Экран 4.2).
    """
    await callback.answer()
    data = await state.get_data()
    total_slides = data.get("total_slides", 0)

    text = i18n.get("tiktok-slideshow-found-msg", total=total_slides)
    await callback.message.edit_text(
        text=text,
        reply_markup=get_tiktok_photo_mode_keyboard(i18n, total_slides)
    )


@router.callback_query(F.data == "tiktok_cancel", StateFilter("*"))
async def tiktok_cancel(callback: CallbackQuery, state: FSMContext):
    """
    Универсальная кнопка Отмена в модуле TikTok.
    """
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await state.clear()


# =====================================================================
# 📌 ПУНКТ 2: АВТОПЕРЕХВАТ ССЫЛОК TIKTOK В ЧАТЕ (Фильтр сообщений)
# =====================================================================

@router.message(StateFilter(None), F.text)
async def auto_download_tiktok_link(message: Message, db_user: User, i18n: I18nContext):
    """
    Автоматически распознает ссылки на TikTok в тексте сообщения и отправляет видео/слайдшоу.
    Работает как в личных сообщениях, так и в группах.
    """
    tiktok_url = TikTokParser.extract_url_from_text(message.text)
    if not tiktok_url:
        return

    logger.info(f"User {db_user.telegram_id} sent TikTok link: {tiktok_url}")
    try:
        await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_video")
    except Exception:
        pass

    info = await TikTokParser.get_post_info(tiktok_url)
    caption = format_user_caption(db_user, tiktok_url)

    short_id = register_post_url(tiktok_url)
    reply_kb = get_tiktok_comments_button_keyboard(short_id, i18n=i18n)

    # 1. Если это фото-слайдшоу
    if info.get("type") == "photo" and info.get("images"):
        images = info["images"]
        media_group = [InputMediaPhoto(media=url, caption=caption if i == 0 else None) for i, url in enumerate(images[:10])]
        try:
            await message.answer_media_group(media=media_group)
            await message.answer(i18n.get("btn-tiktok-comments"), reply_markup=reply_kb)
        except Exception as e:
            logger.error(f"Auto-download photo error: {e}")
            await message.answer(i18n.get("tiktok-auto-photo-error", error=str(e)))
        return

    # 2. Если это обычное видео
    video_file = await TikTokParser.download_video(tiktok_url)
    if video_file and os.path.exists(video_file):
        try:
            video_input = FSInputFile(path=video_file)
            await message.answer_video(video=video_input, caption=caption, reply_markup=reply_kb)
        except Exception as e:
            logger.error(f"Auto-download video error: {e}")
            await message.answer(i18n.get("tiktok-auto-video-error", error=str(e)))
        finally:
            if video_file and os.path.exists(video_file):
                try:
                    os.remove(video_file)
                except Exception:
                    pass
    else:
        await message.answer(i18n.get("tiktok-auto-video-failed"))


from deep_translator import GoogleTranslator

from .keyboards import (
    get_tiktok_account_menu_keyboard,
    get_tiktok_unbind_confirm_keyboard,
    get_tiktok_photo_mode_keyboard,
    get_tiktok_slides_grid_keyboard,
    get_tiktok_cancel_keyboard,
    get_tiktok_comments_button_keyboard,
    get_tiktok_comment_card_keyboard,
)

# Кэш комментариев для мгновенного переключения карточек
_comments_cache = {}

# =====================================================================
# 📌 ПРОСМОТР И ПЕРЕВОД КОММЕНТАРИЕВ TIKTOK (Карточки-карусели)
# =====================================================================

async def render_comment_card(
    callback: CallbackQuery,
    short_id: str,
    index: int,
    is_edit: bool = False,
    translated_text: Optional[str] = None,
    target_lang: str = "ru",
    i18n: Optional[I18nContext] = None
):
    """
    Универсальная функция рендеринга карточки одного комментария с опциональным переводом.
    """
    comments = _comments_cache.get(short_id, [])
    if not comments or index < 1 or index > len(comments):
        err_msg = i18n.get("tiktok-comment-not-found") if i18n else "⚠️ Комментарий не найден."
        await callback.answer(err_msg, show_alert=True)
        return

    comment = comments[index - 1]
    total = len(comments)
    likes_formatted = f"{comment['likes']:,}".replace(",", " ")

    if i18n:
        header = i18n.get("tiktok-comment-header", index=index, total=total)
        author_label = i18n.get("tiktok-comment-author", author=comment['author'])
        likes_label = i18n.get("tiktok-comment-likes", likes=likes_formatted)
        lines = [
            f"{header}\n"
            "───────────────────\n"
            f"{author_label}\n"
            f"{likes_label}\n\n"
            f"💬 <i>«{comment['text']}»</i>"
        ]
        if translated_text:
            lang_label = "русский" if target_lang == "ru" else "English"
            trans_header = i18n.get("tiktok-comment-trans-header", lang=lang_label)
            lines.append(f"\n\n{trans_header}\n<i>«{translated_text}»</i>")
    else:
        lines = [
            f"💬 <b>Комментарий [ {index} из {total} ]</b>\n"
            "───────────────────\n"
            f"👤 <b>Автор:</b> {comment['author']}\n"
            f"❤️ <b>Лайков:</b> {likes_formatted}\n\n"
            f"💬 <i>«{comment['text']}»</i>"
        ]
        if translated_text:
            lang_label = "русский" if target_lang == "ru" else "английский"
            lines.append(f"\n\n🌐 <b>Перевод на {lang_label}:</b>\n<i>«{translated_text}»</i>")

    text = "".join(lines)
    reply_markup = get_tiktok_comment_card_keyboard(
        short_id, index, total, is_translated=bool(translated_text), i18n=i18n
    )

    if is_edit:
        try:
            await callback.message.edit_text(text=text, reply_markup=reply_markup)
        except Exception:
            await callback.message.answer(text=text, reply_markup=reply_markup)
    else:
        await callback.message.answer(text=text, reply_markup=reply_markup)


@router.callback_query(F.data.startswith("tt_comm_"), StateFilter("*"))
async def start_tiktok_comments_card(callback: CallbackQuery, i18n: Optional[I18nContext] = None):
    """
    Показывает первую карточку комментария при клике на '💬 Комментарии'.
    """
    short_id = callback.data.replace("tt_comm_", "")
    url = _post_urls_cache.get(short_id)

    if not url:
        err_msg = i18n.get("tiktok-comments-link-expired") if i18n else "⚠️ Ссылка на пост устарела или не найдена."
        await callback.answer(err_msg, show_alert=True)
        return

    load_msg = i18n.get("tiktok-comments-loading") if i18n else "⏳ Загрузка комментариев..."
    await callback.answer(load_msg)
    res = await TikTokParser.fetch_comments(url, cursor=0, count=15)
    comments = res.get("comments", [])

    if not comments:
        none_msg = i18n.get("tiktok-comments-none") if i18n else "💬 К этому видео не найдено комментариев или они закрыты автором."
        await callback.answer(none_msg, show_alert=True)
        return

    _comments_cache[short_id] = comments
    await render_comment_card(callback, short_id, index=1, is_edit=False, i18n=i18n)


@router.callback_query(F.data.startswith("tt_card_"), StateFilter("*"))
async def navigate_tiktok_comment_card(callback: CallbackQuery, i18n: Optional[I18nContext] = None):
    """
    Переключение карточек комментариев (◀️ Назад / Вперед ▶️).
    """
    await callback.answer()
    parts = callback.data.split("_")
    short_id = parts[2]
    index = int(parts[3])

    await render_comment_card(callback, short_id, index=index, is_edit=True, i18n=i18n)


@router.callback_query(F.data.startswith("tt_tr_"), StateFilter("*"))
async def translate_tiktok_comment_card(callback: CallbackQuery, db_user: User, i18n: Optional[I18nContext] = None):
    """
    Переводит текущий комментарий на выбранный язык пользователя.
    """
    parts = callback.data.split("_")
    short_id = parts[2]
    index = int(parts[3])

    comments = _comments_cache.get(short_id, [])
    if not comments or index < 1 or index > len(comments):
        err_msg = i18n.get("tiktok-comment-not-found") if i18n else "⚠️ Комментарий не найден."
        await callback.answer(err_msg, show_alert=True)
        return

    comment = comments[index - 1]
    target_lang = db_user.language if db_user and db_user.language in ["ru", "en"] else "ru"

    load_msg = i18n.get("tiktok-translation-loading") if i18n else "⏳ Перевод с помощью Google Translate..."
    await callback.answer(load_msg)
    try:
        translated = await asyncio.to_thread(
            lambda: GoogleTranslator(source="auto", target=target_lang).translate(comment["text"])
        )
    except Exception as e:
        logger.error(f"Translation error: {e}")
        err_msg = i18n.get("tiktok-translation-failed") if i18n else "⚠️ Не удалось выполнить перевод."
        await callback.answer(err_msg, show_alert=True)
        return

    await render_comment_card(
        callback,
        short_id=short_id,
        index=index,
        is_edit=True,
        translated_text=translated,
        target_lang=target_lang,
        i18n=i18n
    )


@router.callback_query(F.data == "tiktok_comments_close", StateFilter("*"))
async def close_tiktok_comments(callback: CallbackQuery):
    """
    Удаляет сообщение с карточкой комментариев.
    """
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass

