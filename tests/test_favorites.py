import pytest
from database.repository.favorite_repo import FavoriteTikTokRepository
from database.models.favorite_tiktok import FavoriteTikTok


@pytest.mark.asyncio
async def test_favorite_repository(db_session):
    telegram_id = 999111
    video_id = "7345678901234567890"
    url = "https://www.tiktok.com/@a/video/7345678901234567890"
    title = "Test Favorite Video Title"

    # 1. Проверяем, что изначально не в понравившихся
    is_fav = await FavoriteTikTokRepository.is_favorite(db_session, telegram_id, video_id)
    assert is_fav is False

    # 2. Добавляем в понравившиеся
    added = await FavoriteTikTokRepository.toggle_favorite(db_session, telegram_id, video_id, url, title)
    assert added is True

    # 3. Проверяем наличие и количество
    is_fav = await FavoriteTikTokRepository.is_favorite(db_session, telegram_id, video_id)
    assert is_fav is True

    count = await FavoriteTikTokRepository.count_user_favorites(db_session, telegram_id)
    assert count == 1

    favs = await FavoriteTikTokRepository.get_user_favorites(db_session, telegram_id, limit=5, offset=0)
    assert len(favs) == 1
    assert favs[0].title == title
    assert favs[0].video_id == video_id

    # 4. Удаляем из понравившихся
    removed = await FavoriteTikTokRepository.toggle_favorite(db_session, telegram_id, video_id, url, title)
    assert removed is False

    count_after = await FavoriteTikTokRepository.count_user_favorites(db_session, telegram_id)
    assert count_after == 0


@pytest.mark.asyncio
async def test_favorite_update_title_truncation(db_session):
    """Тест обновления названия и безопасной обрезки до 250 символов в СУБД."""
    telegram_id = 999222
    video_id = "7345678901234567891"
    url = "https://www.tiktok.com/@a/video/7345678901234567891"
    title = "Initial Title"

    await FavoriteTikTokRepository.toggle_favorite(db_session, telegram_id, video_id, url, title)
    favs = await FavoriteTikTokRepository.get_user_favorites(db_session, telegram_id, limit=1, offset=0)
    fav_id = favs[0].id

    # Обновляем очень длинным названием (300 символов)
    long_title = "A" * 300
    updated = await FavoriteTikTokRepository.update_title(db_session, fav_id, long_title)
    assert updated is True

    fav_updated = await FavoriteTikTokRepository.get_by_id(db_session, fav_id)
    assert len(fav_updated.title) <= 250
    assert fav_updated.title == "A" * 250
