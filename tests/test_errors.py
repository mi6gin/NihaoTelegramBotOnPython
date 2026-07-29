import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot
from aiogram.types import ErrorEvent, Update, Message, User
from config.settings import settings
from presentation.telegram.errors.error_handler import (
    error_cache,
    global_error_handler,
)


@pytest.fixture(autouse=True)
def clear_error_cache():
    """Очищает кэш ошибок перед каждым тестом."""
    error_cache.clear()


@pytest.mark.asyncio
async def test_global_error_handler_sends_alert():
    """
    Тестирует отправку алерта админам при падении хендлера.
    """
    # 1. Создаем исключение
    exception = ValueError("Database connection failed")
    
    # 2. Создаем Mock сообщения от пользователя
    user = User(id=123, is_bot=False, first_name="TestUser", username="test_username")
    message = MagicMock(spec=Message)
    message.from_user = user
    message.text = "/profile"
    
    # 3. Создаем Mock события ошибки
    update = MagicMock(spec=Update)
    update.message = message
    update.callback_query = None
    
    event = MagicMock(spec=ErrorEvent)
    event.exception = exception
    event.update = update
    
    # 4. Mock бота и настроек администраторов
    bot = AsyncMock(spec=Bot)
    bot.send_message = AsyncMock()

    with patch.object(settings, "admin_ids", new=[77701, 77702]):
        await global_error_handler(event, bot)
        
        # Проверяем, что бот отправил сообщения обоим админам
        assert bot.send_message.call_count == 2
        
        # Проверяем аргументы отправки сообщения
        calls = bot.send_message.call_args_list
        assert calls[0][1]["chat_id"] == 77701
        assert calls[1][1]["chat_id"] == 77702
        assert "Database connection failed" in calls[0][1]["text"]
        assert "TestUser" in calls[0][1]["text"]
        assert "language-python" in calls[0][1]["text"]  # Наличие разметки трейсбека


@pytest.mark.asyncio
async def test_global_error_handler_throttling():
    """
    Тестирует троттлинг алертов.
    Повторная идентичная ошибка в пределах интервала не должна отправляться повторно.
    """
    exception = AttributeError("NoneType has no attribute 'get'")
    
    user = User(id=123, is_bot=False, first_name="TestUser")
    message = MagicMock(spec=Message)
    message.from_user = user
    message.text = "/start"
    
    update = MagicMock(spec=Update)
    update.message = message
    update.callback_query = None
    
    event = MagicMock(spec=ErrorEvent)
    event.exception = exception
    event.update = update
    
    bot = AsyncMock(spec=Bot)
    bot.send_message = AsyncMock()

    with patch.object(settings, "admin_ids", new=[77701]):
        # 1. Первый вызов — сообщение должно отправиться
        await global_error_handler(event, bot)
        assert bot.send_message.call_count == 1
        
        # Сбрасываем счетчик вызовов
        bot.send_message.reset_mock()
        
        # 2. Второй мгновенный вызов той же самой ошибки — сообщение НЕ должно отправиться (троттлинг)
        await global_error_handler(event, bot)
        assert bot.send_message.call_count == 0
