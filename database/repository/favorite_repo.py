from typing import List, Optional
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.favorite_tiktok import FavoriteTikTok


class FavoriteTikTokRepository:
    """
    Репозиторий для работы с сохраненными понравившимися TikTok-видео.
    """

    @staticmethod
    async def is_favorite(session: AsyncSession, telegram_id: int, video_id: str) -> bool:
        """
        Проверяет, сохранено ли видео в понравившихся у пользователя.
        """
        query = select(FavoriteTikTok).where(
            FavoriteTikTok.telegram_id == telegram_id,
            FavoriteTikTok.video_id == video_id
        )
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def toggle_favorite(session: AsyncSession, telegram_id: int, video_id: str, url: str, title: str) -> bool:
        """
        Инвертирует статус понравившегося видео: добавляет если нет, удаляет если уже сохранено.
        Возвращает True если добавлено, False если удалено.
        """
        query = select(FavoriteTikTok).where(
            FavoriteTikTok.telegram_id == telegram_id,
            FavoriteTikTok.video_id == video_id
        )
        result = await session.execute(query)
        fav = result.scalar_one_or_none()

        if fav:
            await session.delete(fav)
            await session.commit()
            return False
        else:
            new_fav = FavoriteTikTok(
                telegram_id=telegram_id,
                video_id=video_id,
                url=url,
                title=title[:250] if title else "TikTok Video"
            )
            session.add(new_fav)
            await session.commit()
            return True

    @staticmethod
    async def count_user_favorites(session: AsyncSession, telegram_id: int) -> int:
        """
        Возвращает общее количество понравившихся видео у пользователя.
        """
        query = select(func.count(FavoriteTikTok.id)).where(FavoriteTikTok.telegram_id == telegram_id)
        result = await session.execute(query)
        return result.scalar() or 0

    @staticmethod
    async def get_user_favorites(
        session: AsyncSession,
        telegram_id: int,
        limit: int = 5,
        offset: int = 0
    ) -> List[FavoriteTikTok]:
        """
        Получает список понравившихся видео пользователя с поддержкой пагинации (limit/offset).
        """
        query = (
            select(FavoriteTikTok)
            .where(FavoriteTikTok.telegram_id == telegram_id)
            .order_by(FavoriteTikTok.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, fav_id: int) -> Optional[FavoriteTikTok]:
        """
        Получает запись сохраненного видео по внутреннему ID записи.
        """
        query = select(FavoriteTikTok).where(FavoriteTikTok.id == fav_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
