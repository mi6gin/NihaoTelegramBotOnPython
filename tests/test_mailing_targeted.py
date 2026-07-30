import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from presentation.telegram.admin.mailing import (
    start_mailing_panel,
    show_filters_submenu,
    show_themes_submenu,
    process_audience_selection,
    view_target_list,
    toggle_list_user,
    confirm_list_mailing,
    process_mailing_content
)
from database.models.user import User


@pytest.mark.asyncio
async def test_start_mailing_panel():
    callback = MagicMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    state = AsyncMock(spec=FSMContext)
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="audience setup prompt")
    
    await start_mailing_panel(callback, state, i18n)
    
    callback.answer.assert_called_once()
    state.clear.assert_called_once()
    callback.message.edit_text.assert_called_once_with("audience setup prompt", reply_markup=ANY)


@pytest.mark.asyncio
async def test_show_filters_submenu():
    callback = MagicMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="filter selection prompt")
    
    await show_filters_submenu(callback, i18n)
    
    callback.answer.assert_called_once()
    callback.message.edit_text.assert_called_once_with("filter selection prompt", reply_markup=ANY)


@pytest.mark.asyncio
async def test_show_themes_submenu():
    callback = MagicMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="themes selection prompt")
    
    await show_themes_submenu(callback, i18n)
    
    callback.answer.assert_called_once()
    callback.message.edit_text.assert_called_once_with("themes selection prompt", reply_markup=ANY)


@pytest.mark.asyncio
async def test_process_audience_selection():
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "mailing_filter_lang_ru"
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.message_id = 99
    callback.message.edit_text = AsyncMock(return_value=callback.message)
    state = AsyncMock(spec=FSMContext)
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="prompt message text")
    
    await process_audience_selection(callback, state, i18n)
    
    callback.answer.assert_called_once()
    state.set_state.assert_called_once()
    state.update_data.assert_called_once_with(target_filter="lang_ru", target_name="prompt message text", prompt_msg_id=99)


@pytest.mark.asyncio
async def test_view_target_list():
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "mailing_target_list_0"
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    from presentation.telegram.admin.mailing import USERS_CACHE
    USERS_CACHE["users"] = []
    USERS_CACHE["timestamp"] = 0.0

    session = MagicMock(spec=AsyncSession)
    state = AsyncMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={"selected_ids": [123]})
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Select recipients")
    
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=mock_result)
    mock_result.all = MagicMock(return_value=[(123, "Bob", "bob_test")])
    session.execute = AsyncMock(return_value=mock_result)

    await view_target_list(callback, session, state, i18n, page=0)
    
    callback.answer.assert_called_once()
    callback.message.edit_text.assert_called_once()


@pytest.mark.asyncio
async def test_toggle_list_user():
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "mailing_list_toggle_123_0"
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    
    from presentation.telegram.admin.mailing import USERS_CACHE
    USERS_CACHE["users"] = []
    USERS_CACHE["timestamp"] = 0.0

    session = MagicMock(spec=AsyncSession)
    state = AsyncMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={"selected_ids": []})
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Select recipients")
    
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=mock_result)
    mock_result.all = MagicMock(return_value=[(123, "Bob", "bob_test")])
    session.execute = AsyncMock(return_value=mock_result)

    await toggle_list_user(callback, session, state, i18n)
    
    callback.answer.assert_called_once()
    state.update_data.assert_called_once_with(selected_ids=[123])


@pytest.mark.asyncio
async def test_confirm_list_mailing():
    callback = MagicMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.message_id = 88
    callback.message.edit_text = AsyncMock(return_value=callback.message)
    
    state = AsyncMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={"selected_ids": [123]})
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Mailing prompt")

    await confirm_list_mailing(callback, state, i18n)
    
    callback.answer.assert_called_once()
    state.set_state.assert_called_once()
    state.update_data.assert_called_once_with(target_filter="list", target_name="Выборочно (1 чел.)", prompt_msg_id=88)


@pytest.mark.asyncio
async def test_process_mailing_content():
    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    message.copy_to = AsyncMock()
    message.chat = MagicMock()
    message.chat.id = 555
    
    state = AsyncMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={"target_filter": "list", "selected_ids": [123], "prompt_msg_id": 99})
    
    session = MagicMock(spec=AsyncSession)
    bot = AsyncMock(spec=Bot)
    
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Success info")
    
    mock_user = MagicMock(spec=User)
    mock_user.telegram_id = 123
    mock_user.is_banned = False
    
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=mock_result)
    mock_result.all = MagicMock(return_value=[mock_user])
    session.execute = AsyncMock(return_value=mock_result)

    await process_mailing_content(message, state, session, bot, i18n)
    
    state.clear.assert_called_once()
    bot.delete_message.assert_called_once_with(chat_id=555, message_id=99)
    message.copy_to.assert_called_once_with(chat_id=123)
    assert message.answer.call_count == 2
    calls = message.answer.call_args_list
    assert calls[0][0][0] == "Success info"
    assert calls[1][0][0] == "Success info"
    assert "reply_markup" in calls[1][1]
