from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.bot_text import BotText


class BotTextRepository:
    """
    Репозиторий для работы с динамическими текстами бота в СУБД.
    """

    @staticmethod
    async def get_text(session: AsyncSession, key: str, language: str) -> Optional[str]:
        """
        Возвращает пользовательский текст по ключу и языку из БД (или None при отсутствии).
        """
        query = select(BotText.text).where(BotText.key == key, BotText.language == language)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def set_text(session: AsyncSession, key: str, language: str, text: str) -> BotText:
        """
        Создает или обновляет текст по ключу и языку в БД.
        """
        query = select(BotText).where(BotText.key == key, BotText.language == language)
        result = await session.execute(query)
        bot_text = result.scalar_one_or_none()

        if bot_text:
            bot_text.text = text
        else:
            bot_text = BotText(key=key, language=language, text=text)
            session.add(bot_text)

        await session.commit()
        await session.refresh(bot_text)
        return bot_text
