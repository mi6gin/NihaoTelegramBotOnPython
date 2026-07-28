import os
import asyncio
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

@router.callback_query(F.data == "tiktok_account_menu", IsPrivate())
async def show_tiktok_account_menu(callback: CallbackQuery, db_user: User, i18n: I18nContext, state: FSMContext):
    """
    Экран 1.1: Главное окно раздела "Аккаунт TikTok".
    """
    await state.clear()
    await callback.answer()

    if db_user.tiktok_username:
        text = (
            "📱 <b>Раздел «Аккаунт TikTok»</b>\n\n"
            f"┣ <b>Привязанный аккаунт:</b> @{db_user.tiktok_username}\n"
            "┗ <b>Статус:</b> Активен ✅"
        )
    else:
        text = (
            "📱 <b>Раздел «Аккаунт TikTok»</b>\n\n"
            "У вас пока не привязан аккаунт TikTok.\n"
            "Привяжите ваш юзернейм, чтобы использовать персональные возможности!"
        )

    await callback.message.edit_text(
        text=text,
        reply_markup=get_tiktok_account_menu_keyboard(db_user.tiktok_username, i18n)
    )


@router.callback_query(F.data == "tiktok_bind_username", IsPrivate())
async def start_bind_username(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Экран 1.2: Запрос ввода юзернейма TikTok.
    """
    await callback.answer()
    await state.set_state(TikTokStates.waiting_for_username)

    prompt_msg = await callback.message.edit_text(
        "✍️ <b>Отправьте ваш юзернейм в TikTok в чат:</b>\n\n"
        "Пример: <code>@username</code> или <code>username</code>",
        reply_markup=get_tiktok_cancel_keyboard(i18n, callback_data="tiktok_account_menu")
    )
    await state.update_data(prompt_msg_id=prompt_msg.message_id)


@router.message(TikTokStates.waiting_for_username, IsPrivate(), F.text)
async def process_username_input(message: Message, state: FSMContext, session: AsyncSession, db_user: User, i18n: I18nContext):
    """
    Обработка введенного юзернейма TikTok и сохранение в БД.
    """
    raw_username = message.text.strip().lstrip("@")
    if not raw_username or len(raw_username) < 2 or len(raw_username) > 30:
        await message.answer("⚠️ Некорректный юзернейм! Отправьте юзернейм еще раз:")
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
    text = (
        "📱 <b>Раздел «Аккаунт TikTok»</b>\n\n"
        f"┣ <b>Привязанный аккаунт:</b> @{raw_username}\n"
        "┗ <b>Статус:</b> Активен ✅\n\n"
        "✅ <i>Аккаунт успешно привязан!</i>"
    )
    await message.answer(
        text=text,
        reply_markup=get_tiktok_account_menu_keyboard(raw_username, i18n)
    )


@router.callback_query(F.data == "tiktok_unbind_confirm", IsPrivate())
async def tiktok_unbind_confirm(callback: CallbackQuery, db_user: User, i18n: I18nContext):
    """
    Экран 1.3: Подтверждение отвязки аккаунта.
    """
    await callback.answer()
    await callback.message.edit_text(
        f"❓ Вы уверены, что хотите отвязать аккаунт <b>@{db_user.tiktok_username}</b>?",
        reply_markup=get_tiktok_unbind_confirm_keyboard(i18n)
    )


@router.callback_query(F.data == "tiktok_unbind_yes", IsPrivate())
async def tiktok_unbind_yes(callback: CallbackQuery, session: AsyncSession, db_user: User, i18n: I18nContext):
    """
    Отвязывает аккаунт в СУБД и возвращает в меню.
    """
    await callback.answer("Аккаунт отвязан!", show_alert=True)
    await UserRepository.set_tiktok_username(session, db_user.telegram_id, None)
    
    text = (
        "📱 <b>Раздел «Аккаунт TikTok»</b>\n\n"
        "У вас пока не привязан аккаунт TikTok.\n"
        "Привяжите ваш юзернейм, чтобы использовать персональные возможности!"
    )
    await callback.message.edit_text(
        text=text,
        reply_markup=get_tiktok_account_menu_keyboard(None, i18n)
    )


# =====================================================================
# 📌 ПУНКТ 3: МИКРО-МЕНЮ /Mtiktok (Только звук MP3)
# =====================================================================

@router.message(Command("Mtiktok"), IsPrivate())
async def cmd_mtiktok(message: Message, state: FSMContext, i18n: I18nContext):
    """
    Старт микро-меню /Mtiktok (Скачивание только аудио).
    """
    await state.clear()
    await state.set_state(TikTokStates.waiting_for_audio_link)

    prompt_msg = await message.answer(
        "🎵 <b>Микро-меню: Скачивание аудио из TikTok</b>\n\n"
        "Отправьте ссылку на видео TikTok в чат, чтобы получить оригинальный аудиотрек в формате MP3.",
        reply_markup=get_tiktok_cancel_keyboard(i18n, callback_data="tiktok_cancel")
    )
    await state.update_data(prompt_msg_id=prompt_msg.message_id)


@router.message(TikTokStates.waiting_for_audio_link, IsPrivate(), F.text)
async def process_audio_link_input(message: Message, state: FSMContext, db_user: User, i18n: I18nContext):
    """
    Обработка ссылки для получения аудио MP3.
    """
    tiktok_url = TikTokParser.extract_url_from_text(message.text)
    if not tiktok_url:
        await message.answer("⚠️ Ссылка на TikTok не распознана! Отправьте корректную ссылку:")
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
    audio_file = await TikTokParser.download_audio(tiktok_url)

    if not audio_file or not os.path.exists(audio_file):
        await message.answer("❌ К сожалению, не удалось извлечь аудиозапись из этого TikTok.")
        await state.clear()
        return

    caption = format_user_caption(db_user, tiktok_url)
    try:
        await message.answer_document(
            document=FSInputFile(path=audio_file),
            caption=caption
        )
    except Exception as e:
        logger.error(f"Error sending audio file: {e}")
        await message.answer("❌ Ошибка при отправке аудиофайла.")
    finally:
        if audio_file and os.path.exists(audio_file):
            try:
                os.remove(audio_file)
            except Exception:
                pass

    await state.clear()


# =====================================================================
# 📌 ПУНКТ 4: МИКРО-МЕНЮ /Ptiktok (Слайдшоу / Карусели картинок)
# =====================================================================

@router.message(Command("Ptiktok"), IsPrivate())
async def cmd_ptiktok(message: Message, state: FSMContext, i18n: I18nContext):
    """
    Старт микро-меню /Ptiktok (Скачивание слайдшоу).
    """
    await state.clear()
    await state.set_state(TikTokStates.waiting_for_photo_link)

    prompt_msg = await message.answer(
        "🖼️ <b>Микро-меню: Скачивание слайдшоу из TikTok</b>\n\n"
        "Отправьте ссылку на фото-карусель (слайдшоу) TikTok.",
        reply_markup=get_tiktok_cancel_keyboard(i18n, callback_data="tiktok_cancel")
    )
    await state.update_data(prompt_msg_id=prompt_msg.message_id)


@router.message(TikTokStates.waiting_for_photo_link, IsPrivate(), F.text)
async def process_photo_link_input(message: Message, state: FSMContext, i18n: I18nContext):
    """
    Обработка ссылки на слайдшоу и переход в окно выбора режима (Экран 4.2).
    """
    tiktok_url = TikTokParser.extract_url_from_text(message.text)
    if not tiktok_url:
        await message.answer("⚠️ Ссылка на TikTok не распознана! Отправьте корректную ссылку:")
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
        await message.answer("❌ По этой ссылке не найдено карусели картинок/слайдшоу.")
        await state.clear()
        return

    total_slides = len(images)
    await state.update_data(
        tiktok_url=tiktok_url,
        images=images,
        total_slides=total_slides,
        selected_slides=list()
    )

    text = f"📸 <b>Найдено слайдшоу! Всего слайдов: {total_slides}</b>\n\nВыберите, как вы хотите скачать картинки:"
    await message.answer(
        text=text,
        reply_markup=get_tiktok_photo_mode_keyboard(i18n, total_slides)
    )


@router.callback_query(F.data == "tiktok_photo_all", IsPrivate())
async def download_all_slides(callback: CallbackQuery, state: FSMContext, db_user: User):
    """
    Скачивание всех картинок из слайдшоу альбомом.
    """
    await callback.answer()
    data = await state.get_data()
    images = data.get("images", [])
    tiktok_url = data.get("tiktok_url", "")

    if not images:
        await callback.message.answer("❌ Ошибка данных слайдшоу.")
        await state.clear()
        return

    caption = format_user_caption(db_user, tiktok_url)
    media_group = [InputMediaPhoto(media=url, caption=caption if i == 0 else None) for i, url in enumerate(images[:10])]

    try:
        await callback.message.answer_media_group(media=media_group)
    except Exception as e:
        logger.error(f"Error sending media group: {e}")
        await callback.message.answer("❌ Ошибка при отправке слайдов.")

    await state.clear()


@router.callback_query(F.data == "tiktok_photo_select_mode", IsPrivate())
async def enter_slides_selection_mode(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Переход в интерактивную сетку выбора конкретных слайдов (Экран 4.3).
    """
    await callback.answer()
    data = await state.get_data()
    total_slides = data.get("total_slides", 0)
    selected_slides = set(data.get("selected_slides", []))

    await state.set_state(TikTokStates.selecting_slides)

    text = (
        "🔢 <b>Нажимайте на кнопки с номерами слайдов, чтобы отметить нужные:</b>\n\n"
        f"Отмечено для скачивания: [ {', '.join(map(str, sorted(selected_slides)))} ]"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=get_tiktok_slides_grid_keyboard(total_slides, selected_slides, i18n)
    )


@router.callback_query(F.data.startswith("tiktok_toggle_slide_"), TikTokStates.selecting_slides, IsPrivate())
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

    text = (
        "🔢 <b>Нажимайте на кнопки с номерами слайдов, чтобы отметить нужные:</b>\n\n"
        f"Отмечено для скачивания: [ {', '.join(map(str, sorted(selected_slides)))} ]"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=get_tiktok_slides_grid_keyboard(total_slides, selected_slides, i18n)
    )


@router.callback_query(F.data == "tiktok_download_selected", TikTokStates.selecting_slides, IsPrivate())
async def download_selected_slides(callback: CallbackQuery, state: FSMContext, db_user: User):
    """
    Скачивание только отфильтрованных слайдов с проверкой на пустой выбор.
    """
    data = await state.get_data()
    images = data.get("images", [])
    tiktok_url = data.get("tiktok_url", "")
    selected_slides = sorted(list(set(data.get("selected_slides", []))))

    if not selected_slides:
        await callback.answer("⚠️ Вы не выбрали ни одного слайда! Отметьте нужные цифры.", show_alert=True)
        return

    await callback.answer()
    caption = format_user_caption(db_user, tiktok_url)
    
    selected_image_urls = [images[i - 1] for i in selected_slides if 0 <= i - 1 < len(images)]
    media_group = [InputMediaPhoto(media=url, caption=caption if idx == 0 else None) for idx, url in enumerate(selected_image_urls[:10])]

    try:
        await callback.message.answer_media_group(media=media_group)
    except Exception as e:
        logger.error(f"Error sending selected slides: {e}")
        await callback.message.answer("❌ Ошибка при отправке выбранных слайдов.")

    await state.clear()


@router.callback_query(F.data == "tiktok_photo_back_mode", TikTokStates.selecting_slides, IsPrivate())
async def back_to_photo_mode(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Возврат из сетки слайдов на выбор режима (Экран 4.2).
    """
    await callback.answer()
    data = await state.get_data()
    total_slides = data.get("total_slides", 0)

    text = f"📸 <b>Найдено слайдшоу! Всего слайдов: {total_slides}</b>\n\nВыберите, как вы хотите скачать картинки:"
    await callback.message.edit_text(
        text=text,
        reply_markup=get_tiktok_photo_mode_keyboard(i18n, total_slides)
    )


@router.callback_query(F.data == "tiktok_cancel", IsPrivate(), StateFilter("*"))
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

@router.message(IsPrivate(), StateFilter(None), F.text)
async def auto_download_tiktok_link(message: Message, db_user: User):
    """
    Автоматически распознает ссылки на TikTok в тексте сообщения и отправляет видео/слайдшоу.
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
    reply_kb = get_tiktok_comments_button_keyboard(short_id)

    # 1. Если это фото-слайдшоу
    if info.get("type") == "photo" and info.get("images"):
        images = info["images"]
        media_group = [InputMediaPhoto(media=url, caption=caption if i == 0 else None) for i, url in enumerate(images[:10])]
        try:
            await message.answer_media_group(media=media_group)
            await message.answer("💬 Комментарии к этому слайдшоу:", reply_markup=reply_kb)
        except Exception as e:
            logger.error(f"Auto-download photo error: {e}")
            await message.answer(f"❌ Ошибка при отправке слайдшоу: {e}")
        return

    # 2. Если это обычное видео
    video_file = await TikTokParser.download_video(tiktok_url)
    if video_file and os.path.exists(video_file):
        try:
            video_input = FSInputFile(path=video_file)
            await message.answer_video(video=video_input, caption=caption, reply_markup=reply_kb)
        except Exception as e:
            logger.error(f"Auto-download video error: {e}")
            await message.answer(f"❌ Ошибка при отправке видео: {e}")
        finally:
            if video_file and os.path.exists(video_file):
                try:
                    os.remove(video_file)
                except Exception:
                    pass
    else:
        await message.answer("❌ К сожалению, не удалось скачать это видео из TikTok.")


from .keyboards import (
    get_tiktok_account_menu_keyboard,
    get_tiktok_unbind_confirm_keyboard,
    get_tiktok_photo_mode_keyboard,
    get_tiktok_slides_grid_keyboard,
    get_tiktok_cancel_keyboard,
    get_tiktok_comments_button_keyboard,
    get_tiktok_comments_pagination_keyboard,
)

# =====================================================================
# 📌 ПРОСМОТР И ПАГИНАЦИЯ КОММЕНТАРИЕВ TIKTOK
# =====================================================================

@router.callback_query(F.data.startswith("tt_comm_"), IsPrivate(), StateFilter("*"))
async def show_tiktok_comments(callback: CallbackQuery):
    """
    Показывает первую страницу комментариев к посту TikTok с кнопками пагинации.
    """
    data = callback.data.replace("tt_comm_", "")
    if data.startswith("page_"):
        parts = data.split("_")
        short_id = parts[1]
        cursor = int(parts[2])
        is_edit = True
    else:
        short_id = data
        cursor = 0
        is_edit = False

    url = _post_urls_cache.get(short_id)
    if not url:
        await callback.answer("⚠️ Ссылка на пост устарела или не найдена.", show_alert=True)
        return

    await callback.answer("⏳ Загрузка комментариев...")
    res = await TikTokParser.fetch_comments(url, cursor=cursor, count=5)
    comments = res.get("comments", [])
    has_more = res.get("has_more", False)

    if not comments:
        await callback.answer("💬 Больше нет комментариев или они закрыты автором.", show_alert=True)
        return

    page_num = (cursor // 5) + 1
    lines = [f"💬 <b>Комментарии TikTok (Стр. {page_num}):</b>\n"]
    for idx, c in enumerate(comments, cursor + 1):
        lines.append(f"{idx}. 👤 <b>{c['author']}</b> (❤️ {c['likes']}):\n   <i>«{c['text']}»</i>\n")

    reply_markup = get_tiktok_comments_pagination_keyboard(short_id, cursor, has_more)

    if is_edit:
        try:
            await callback.message.edit_text(text="\n".join(lines), reply_markup=reply_markup)
        except Exception:
            await callback.message.answer(text="\n".join(lines), reply_markup=reply_markup)
    else:
        await callback.message.answer(text="\n".join(lines), reply_markup=reply_markup)


@router.callback_query(F.data == "tiktok_comments_close", IsPrivate(), StateFilter("*"))
async def close_tiktok_comments(callback: CallbackQuery):
    """
    Удаляет сообщение с комментариями.
    """
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass

