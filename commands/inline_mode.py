from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultCachedVideo,
    InlineQueryResultVideo,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository.favorite_repo import FavoriteTikTokRepository
from infrastructure.tiktok import TikTokParser

router = Router(name="inline_mode_router")

TIKTOK_ICON = "https://cdn-icons-png.flaticon.com/512/3046/3046124.png"


@router.inline_query()
async def inline_favorites_query(inline_query: InlineQuery, session: AsyncSession, i18n: I18nContext):
    """
    Обработчик инлайн-поиска по сохраненным «Понравившимся» видео пользователя.
    Гарантированно высылает САМО ВИДЕО (InlineQueryResultCachedVideo / InlineQueryResultVideo),
    а не текстовую ссылку.
    """
    user_id = inline_query.from_user.id
    query_text = inline_query.query.strip().lower()

    favorites = await FavoriteTikTokRepository.get_user_favorites(session, telegram_id=user_id, limit=50)

    results = []

    if not favorites:
        results.append(
            InlineQueryResultArticle(
                id="empty_fav",
                title=i18n.get("favorites-inline-empty-title"),
                description=i18n.get("favorites-inline-empty-desc"),
                thumbnail_url=TIKTOK_ICON,
                input_message_content=InputTextMessageContent(
                    message_text=i18n.get("favorites-inline-empty-desc"),
                    parse_mode="HTML"
                )
            )
        )
    else:
        # Фильтруем тиктоки по названию или ссылке, если пользователь ввел текст
        matching_favs = [
            fav for fav in favorites
            if not query_text or query_text in fav.title.lower() or query_text in fav.url.lower()
        ]

        if not matching_favs:
            results.append(
                InlineQueryResultArticle(
                    id="no_match",
                    title=i18n.get("favorites-inline-no-match-title"),
                    description=i18n.get("favorites-inline-no-match-desc", query=query_text),
                    thumbnail_url=TIKTOK_ICON,
                    input_message_content=InputTextMessageContent(
                        message_text=i18n.get("favorites-inline-no-match-desc", query=query_text),
                        parse_mode="HTML"
                    )
                )
            )
        else:
            for fav in matching_favs[:50]:
                caption = f"🎬 <b>{fav.title}</b>\n\n<a href=\"{fav.url}\">Ссылка на TikTok</a>"

                if fav.file_id:
                    # 1. Если есть telegram file_id -> мгновенно высылаем закэшированное видео
                    results.append(
                        InlineQueryResultCachedVideo(
                            id=f"fav_{fav.id}",
                            video_file_id=fav.file_id,
                            title=f"❤️ {fav.title}",
                            description=f"Отправить видео • {fav.url}",
                            caption=caption,
                            parse_mode="HTML"
                        )
                    )
                else:
                    # 2. Если file_id нет в БД (старые записи) -> запрашиваем прямую ссылку MP4 через API
                    tikwm_info = await TikTokParser.fetch_tikwm_info(fav.url)
                    play_url = tikwm_info.get("play_url") if tikwm_info else None
                    cover_url = tikwm_info.get("cover") if tikwm_info else None

                    if play_url:
                        results.append(
                            InlineQueryResultVideo(
                                id=f"fav_{fav.id}",
                                video_url=play_url,
                                mime_type="video/mp4",
                                thumbnail_url=cover_url or TIKTOK_ICON,
                                title=f"❤️ {fav.title}",
                                description=f"Отправить видео • {fav.url}",
                                caption=caption,
                                parse_mode="HTML"
                            )
                        )
                    else:
                        # Резервный вариант, если MP4 недоступен
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text=i18n.get("btn-inline-watch"), url=fav.url)]
                        ])
                        content_text = i18n.get(
                            "favorites-inline-share-text",
                            title=fav.title,
                            link=fav.url,
                            user=inline_query.from_user.first_name
                        )
                        results.append(
                            InlineQueryResultArticle(
                                id=f"fav_{fav.id}",
                                title=f"❤️ {fav.title}",
                                description=f"TikTok • {fav.url}",
                                thumbnail_url=TIKTOK_ICON,
                                input_message_content=InputTextMessageContent(
                                    message_text=content_text,
                                    parse_mode="HTML"
                                ),
                                reply_markup=keyboard
                            )
                        )

    await inline_query.answer(results, cache_time=5, is_personal=True)
