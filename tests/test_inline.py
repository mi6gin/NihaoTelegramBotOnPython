import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import InlineQuery
from database.repository.favorite_repo import FavoriteTikTokRepository
from database.models.favorite_tiktok import FavoriteTikTok
from commands.inline_mode import inline_favorites_query
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_inline_favorites_query_empty(db_session: AsyncSession):
    """Проверяет ответ инлайн-режима, когда у пользователя нет сохраненных тиктоков."""
    inline_query = MagicMock(spec=InlineQuery)
    inline_query.from_user = MagicMock(id=99999, first_name="TestUser")
    inline_query.query = ""
    inline_query.answer = AsyncMock()

    i18n = MagicMock()
    i18n.get = MagicMock(side_effect=lambda key, **kwargs: f"text_{key}")

    await inline_favorites_query(inline_query, db_session, i18n)

    inline_query.answer.assert_called_once()
    results = inline_query.answer.call_args[0][0]
    assert len(results) == 1
    assert results[0].id == "empty_fav"


@pytest.mark.asyncio
async def test_inline_favorites_query_with_items(db_session: AsyncSession):
    """Проверяет фильтрацию и вычурный вывод списка понравившихся в инлайн-режиме."""
    user_id = 88888
    await FavoriteTikTokRepository.toggle_favorite(
        session=db_session,
        telegram_id=user_id,
        video_id="732918239103847293",
        url="https://www.tiktok.com/@test/video/732918239103847293",
        title="Смешной котик"
    )

    inline_query = MagicMock(spec=InlineQuery)
    inline_query.from_user = MagicMock(id=user_id, first_name="CatLover")
    inline_query.query = "котик"
    inline_query.answer = AsyncMock()

    i18n = MagicMock()
    i18n.get = MagicMock(side_effect=lambda key, **kwargs: f"text_{key}")

    await inline_favorites_query(inline_query, db_session, i18n)

    inline_query.answer.assert_called_once()
    results = inline_query.answer.call_args[0][0]
    assert len(results) == 1
    assert "fav_" in results[0].id
    assert "котик" in results[0].title.lower()


@pytest.mark.asyncio
async def test_inline_favorites_query_cached_video(db_session: AsyncSession):
    """Проверяет генерацию InlineQueryResultCachedVideo с настоящим file_id."""
    from aiogram.types import InlineQueryResultCachedVideo
    user_id = 77777
    await FavoriteTikTokRepository.toggle_favorite(
        session=db_session,
        telegram_id=user_id,
        video_id="732918239103847999",
        url="https://www.tiktok.com/@test/video/732918239103847999",
        title="Танцующий пес",
        file_id="BAACAgIAAxkBAAITestFileId123"
    )

    inline_query = MagicMock(spec=InlineQuery)
    inline_query.from_user = MagicMock(id=user_id, first_name="DogFan")
    inline_query.query = ""
    inline_query.answer = AsyncMock()

    i18n = MagicMock()
    i18n.get = MagicMock(side_effect=lambda key, **kwargs: f"text_{key}")

    await inline_favorites_query(inline_query, db_session, i18n)

    inline_query.answer.assert_called_once()
    results = inline_query.answer.call_args[0][0]
    assert len(results) == 1
    assert isinstance(results[0], InlineQueryResultCachedVideo)
    assert results[0].video_file_id == "BAACAgIAAxkBAAITestFileId123"

