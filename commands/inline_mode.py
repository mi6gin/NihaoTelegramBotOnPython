from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository.favorite_repo import FavoriteTikTokRepository

router = Router(name="inline_mode_router")

TIKTOK_ICON = "https://cdn-icons-png.flaticon.com/512/3046/3046124.png"


@router.inline_query()
async def inline_favorites_query(inline_query: InlineQuery, session: AsyncSession, i18n: I18nContext):
    """
    Обработчик инлайн-поиска по сохраненным «Понравившимся» видео пользователя.
    Работает в любом чате Telegram при вводе @bot_username.
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
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=i18n.get("btn-inline-watch"),
                            url=fav.url
                        )
                    ]
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
                            parse_mode="HTML",
                            disable_web_page_preview=False
                        ),
                        reply_markup=keyboard
                    )
                )

    await inline_query.answer(results, cache_time=5, is_personal=True)
