import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram_i18n import I18nContext

from commands.support import process_cancel_support
from routers.admin.mailing import process_cancel_mailing
from routers.admin.users import process_cancel_manage_users


@pytest.mark.asyncio
async def test_process_cancel_support():
    """Тест отмены FSM поддержки: проверяет сброс состояния и смену меню."""
    callback = MagicMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    
    state = AsyncMock(spec=FSMContext)
    db_user = MagicMock()
    db_user.role = "user"
    
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Support Title")

    with patch("commands.support.IsAdmin") as mock_is_admin:
        # Мокаем проверку на админа
        mock_is_admin.return_value = AsyncMock(return_value=False)
        
        await process_cancel_support(callback, state, db_user, i18n)
        
        callback.answer.assert_called_once()
        state.clear.assert_called_once()
        callback.message.edit_text.assert_called_once()


@pytest.mark.asyncio
async def test_process_cancel_mailing():
    """Тест отмены FSM рассылки: проверяет сброс состояния и возврат в админку."""
    callback = MagicMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    
    state = AsyncMock(spec=FSMContext)
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Mailing Title")

    await process_cancel_mailing(callback, state, i18n)
    
    assert callback.answer.call_count == 2
    assert state.clear.call_count == 2
    callback.message.edit_text.assert_called_once()


@pytest.mark.asyncio
async def test_process_cancel_manage_users():
    """Тест отмены FSM управления пользователями: проверяет сброс состояния и возврат в админку."""
    callback = MagicMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    
    state = AsyncMock(spec=FSMContext)
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Manage Title")

    await process_cancel_manage_users(callback, state, i18n)
    
    callback.answer.assert_called_once()
    state.clear.assert_called_once()
    callback.message.edit_text.assert_called_once()
