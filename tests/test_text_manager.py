import pytest
from unittest.mock import MagicMock
from aiogram_i18n import I18nContext

from utils.text_manager import DynamicTextManager
from database.repository.bot_text_repo import BotTextRepository


@pytest.mark.asyncio
async def test_dynamic_text_manager_ram_cache(db_session):
    """Тест работы DynamicTextManager: скорость, кэширование в RAM и fallback на i18n."""
    manager = DynamicTextManager()

    i18n_ru = MagicMock(spec=I18nContext)
    i18n_ru.locale = "ru"
    i18n_ru.get = MagicMock(return_value="Стандартный FTL текст")

    # 1. Проверяем фолбек на .ftl, если в RAM кэше ничего нет
    res1 = manager.get_text("dedinside-title", i18n_ru)
    assert res1 == "Стандартный FTL текст"
    i18n_ru.get.assert_called_once_with("dedinside-title")

    # 2. Обновляем текст через set_text (сохраняет в БД и RAM)
    custom_ru = "Кастомный текст из СУБД/RAM"
    await manager.set_text(db_session, "dedinside-title", "ru", custom_ru)

    # 3. Проверяем, что кэш отдается за 0ms из RAM без обращения к i18n.get
    i18n_ru.get.reset_mock()
    res2 = manager.get_text("dedinside-title", i18n_ru)
    assert res2 == custom_ru
    i18n_ru.get.assert_not_called()

    # 4. Проверяем повторную загрузку всего кэша из БД (при старте бота)
    new_manager = DynamicTextManager()
    await new_manager.load_cache(db_session)
    assert new_manager.get_text("dedinside-title", i18n_ru) == custom_ru
