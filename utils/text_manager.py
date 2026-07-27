from typing import Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram_i18n import I18nContext
from database.models.bot_text import BotText
from utils.logger import logger


class DynamicTextManager:
    """
    In-Memory кэш-менеджер для динамических переводов бота.
    Считывает тексты из СУБД в оперативную память для молниеносного (0ms) доступа без нагрузок на БД.
    Обеспечивает гибридный выбор: RAM Кэш -> Fallback на Fluent i18n (.ftl).
    """

    def __init__(self):
        # Кэш в оперативной памяти: {"key:language": "text"}
        self._cache: Dict[str, str] = {}
        self._loaded: bool = False

    async def load_cache(self, session: AsyncSession) -> None:
        """
        Загружает все пользовательские тексты из СУБД в кэш оперативной памяти.
        Вызывается при старте бота и при обновлении текстов.
        """
        try:
            query = select(BotText)
            result = await session.execute(query)
            bot_texts = result.scalars().all()

            self._cache.clear()
            for item in bot_texts:
                cache_key = f"{item.key}:{item.language}"
                self._cache[cache_key] = item.text

            self._loaded = True
            logger.info(f"DynamicTextManager: Загружено {len(self._cache)} динамических текстов из СУБД в кэш RAM.")
        except Exception as e:
            logger.error(f"DynamicTextManager: Ошибка загрузки кэша текстов из БД: {e}")

    def get_text(self, key: str, i18n: I18nContext, **kwargs) -> str:
        """
        Возвращает текст с молниеносной скоростью:
        1. Из RAM Кэша (если админ настроил его через БД/панель)
        2. Иначе из статичных файлов Fluent .ftl (стандарт проекта)
        """
        cache_key = f"{key}:{i18n.locale}"
        if cache_key in self._cache:
            text = self._cache[cache_key]
            if kwargs:
                try:
                    text = text.format(**kwargs)
                except Exception:
                    pass
            return text

        return i18n.get(key, **kwargs)

    async def set_text(self, session: AsyncSession, key: str, language: str, text: str) -> None:
        """
        Сохраняет новый текст в СУБД и мгновенно обновляет кэш в RAM.
        """
        from database.repository.bot_text_repo import BotTextRepository
        await BotTextRepository.set_text(session, key, language, text)

        cache_key = f"{key}:{language}"
        self._cache[cache_key] = text
        logger.info(f"DynamicTextManager: Текст '{key}' ({language}) обновлен в RAM кэше.")


# Единый глобальный объект кэш-менеджера
text_manager = DynamicTextManager()
