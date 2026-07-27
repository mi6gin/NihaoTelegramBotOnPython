import pytest
from database.models.bot_text import BotText
from database.repository.bot_text_repo import BotTextRepository


@pytest.mark.asyncio
async def test_bot_text_repo_crud(db_session):
    """Интеграционный тест создания, чтения и обновления пользовательских текстов в БД."""
    # Пытаемся получить несуществующий текст
    initial_text = await BotTextRepository.get_text(db_session, "dedinside_title", "ru")
    assert initial_text is None

    # Создаем новый текст RU
    new_ru = "Здравствуйте бояре из БД!"
    created = await BotTextRepository.set_text(db_session, "dedinside_title", "ru", new_ru)
    assert created.text == new_ru

    # Проверяем чтение созданного текста
    fetched_ru = await BotTextRepository.get_text(db_session, "dedinside_title", "ru")
    assert fetched_ru == new_ru

    # Обновляем текст RU
    updated_ru = "Обновленное приветствие из БД!"
    await BotTextRepository.set_text(db_session, "dedinside_title", "ru", updated_ru)
    fetched_updated = await BotTextRepository.get_text(db_session, "dedinside_title", "ru")
    assert fetched_updated == updated_ru

    # Проверяем независимость от EN локали
    fetched_en = await BotTextRepository.get_text(db_session, "dedinside_title", "en")
    assert fetched_en is None
