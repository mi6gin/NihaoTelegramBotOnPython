import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message
from middlewares.throttling_mw import ThrottlingMiddleware
from middlewares.ban_mw import BanMiddleware
from database.repository.user_repo import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_throttling_middleware_block_spam():
    """Тест троттлинг-мидлвари: первое сообщение проходит, второе блокируется (спам)."""
    middleware = ThrottlingMiddleware(limit=1.0)
    handler = AsyncMock(return_value="handler_response")

    # Создаем mock-сообщение
    message = MagicMock(spec=Message)
    message.from_user = MagicMock()
    message.from_user.id = 12345

    data = {}

    # Первый запрос — должен успешно пройти в обработчик
    res1 = await middleware(handler, message, data)
    assert res1 == "handler_response"
    assert handler.call_count == 1

    # Второй мгновенный запрос — должен заблокироваться (handler не должен вызваться повторно)
    res2 = await middleware(handler, message, data)
    assert res2 is None
    assert handler.call_count == 1  # Счетчик вызовов остался прежним
    
    
@pytest.mark.asyncio
async def test_ban_middleware_allows_active_user(db_session: AsyncSession):
    """Проверяет, что BanMiddleware регистрирует активного юзера и пропускает его дальше."""
    middleware = BanMiddleware()
    handler = AsyncMock(return_value="allowed")
    
    message = MagicMock(spec=Message)
    tg_user = MagicMock()
    tg_user.id = 77701
    tg_user.username = "active_guy"
    tg_user.first_name = "Alex"
    tg_user.last_name = "Smith"
    
    message.from_user = tg_user
    
    data = {
        "session": db_session,
        "event_from_user": tg_user
    }
    
    result = await middleware(handler, message, data)
    assert result == "allowed"
    assert handler.call_count == 1
    
    # Объект db_user должен быть добавлен в data
    assert "db_user" in data
    assert data["db_user"].telegram_id == 77701
    assert data["db_user"].is_banned is False


@pytest.mark.asyncio
async def test_ban_middleware_blocks_banned_user(db_session: AsyncSession):
    """Проверяет, что BanMiddleware блокирует забаненного юзера и не пускает его в хендлер."""
    user_id = 77702
    
    # 1. Сначала регистрируем и баним пользователя в тестовой БД
    await UserRepository.get_or_create(db_session, user_id, first_name="BadGuy")
    await UserRepository.set_ban_status(db_session, user_id, is_banned=True)
    
    middleware = BanMiddleware()
    handler = AsyncMock(return_value="should_not_run")
    
    message = AsyncMock(spec=Message)
    tg_user = MagicMock()
    tg_user.id = user_id
    tg_user.username = "banned_guy"
    tg_user.first_name = "BadGuy"
    tg_user.last_name = None
    
    message.from_user = tg_user
    message.answer = AsyncMock() # Mock ответа пользователю
    
    data = {
        "session": db_session,
        "event_from_user": tg_user
    }
    
    result = await middleware(handler, message, data)
    assert result is None # Запрос отклонен
    assert handler.call_count == 0 # Обработчик не вызывался
    
    # Сообщение о блокировке должно быть отправлено пользователю
    message.answer.assert_called_once()
    assert "заблокированы" in message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_logging_middleware_message(caplog):
    """Тест LoggingMiddleware: проверяет логирование входящего текстового сообщения."""
    from middlewares.logging_mw import LoggingMiddleware
    import logging

    middleware = LoggingMiddleware()
    handler = AsyncMock(return_value="response")

    # Создаем mock-сообщение
    message = MagicMock(spec=Message)
    message.text = "Hello world!"
    message.contact = None
    
    tg_user = MagicMock()
    tg_user.id = 112233
    tg_user.username = "test_log_user"

    data = {
        "event_from_user": tg_user
    }

    with caplog.at_level(logging.INFO):
        res = await middleware(handler, message, data)
        assert res == "response"
        assert any("sent text message: 'Hello world!'" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_logging_middleware_callback_query(caplog):
    """Тест LoggingMiddleware: проверяет логирование нажатия inline-кнопки."""
    from middlewares.logging_mw import LoggingMiddleware
    from aiogram.types import CallbackQuery
    import logging

    middleware = LoggingMiddleware()
    handler = AsyncMock(return_value="response")

    # Создаем mock CallbackQuery
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "click_button_abc"
    
    tg_user = MagicMock()
    tg_user.id = 112233
    tg_user.username = "test_log_user"

    data = {
        "event_from_user": tg_user
    }

    with caplog.at_level(logging.INFO):
        res = await middleware(handler, callback, data)
        assert res == "response"
        assert any("clicked inline button with callback_data: 'click_button_abc'" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_menu_owner_middleware():
    """Тест MenuOwnerMiddleware: пускает владельца меню и блокирует стороннего пользователя."""
    from middlewares.menu_owner_mw import MenuOwnerMiddleware
    from aiogram.types import CallbackQuery

    middleware = MenuOwnerMiddleware()
    handler = AsyncMock(return_value="allowed")

    # 1. Владелец меню (ID 1000) кликает по своей кнопке
    callback_owner = MagicMock(spec=CallbackQuery)
    callback_owner.data = "user_profile:1000"
    callback_owner.from_user = MagicMock(id=1000)
    callback_owner.answer = AsyncMock()

    res_owner = await middleware(handler, callback_owner, {})
    assert res_owner == "allowed"
    assert handler.call_count == 1

    # 2. Другой пользователь (ID 2000) пытаются кликнуть по чужой кнопке
    callback_stranger = MagicMock(spec=CallbackQuery)
    callback_stranger.data = "user_profile:1000"
    callback_stranger.from_user = MagicMock(id=2000)
    callback_stranger.answer = AsyncMock()

    res_stranger = await middleware(handler, callback_stranger, {})
    assert res_stranger is None
    assert handler.call_count == 1  # Обработчик не вызвался повторно!
    callback_stranger.answer.assert_called_once()


