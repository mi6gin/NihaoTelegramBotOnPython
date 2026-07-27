import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram_i18n import I18nContext

from commands.dedinside import (
    DedinsideStates,
    cmd_dedinside,
    process_dedinside_cancel,
    process_count_selection,
    process_non_text_message,
    process_spam_text_message,
)


@pytest.mark.asyncio
async def test_cmd_dedinside_when_clear():
    """Тест вызова /dedinside при свободном FSM состоянии."""
    message = MagicMock(spec=Message)
    message.answer = AsyncMock(return_value=MagicMock(message_id=100))
    
    state = AsyncMock(spec=FSMContext)
    state.get_state = AsyncMock(return_value=None)
    state.set_state = AsyncMock()
    state.update_data = AsyncMock()

    i18n = MagicMock(spec=I18nContext)
    i18n.locale = "ru"
    i18n.get = MagicMock(return_value="Title")

    with patch("commands.dedinside.text_manager.get_text", return_value="Title"):
        await cmd_dedinside(message, state, i18n)

    message.answer.assert_called_once()
    state.set_state.assert_called_once_with(DedinsideStates.selecting_count)
    state.update_data.assert_called_once_with(menu_msg_id=100)


@pytest.mark.asyncio
async def test_cmd_dedinside_when_already_active():
    """Тест вызова /dedinside при уже активном FSM состоянии (должна блокироваться)."""
    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    
    state = AsyncMock(spec=FSMContext)
    state.get_state = AsyncMock(return_value=DedinsideStates.selecting_count)

    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Already Active Warning")

    with patch("commands.dedinside.text_manager.get_text", return_value="Already Active Warning"):
        await cmd_dedinside(message, state, i18n)

    message.answer.assert_called_once_with("Already Active Warning")


@pytest.mark.asyncio
async def test_process_dedinside_cancel():
    """Тест нажатия инлайн-кнопки Отмена."""
    callback = MagicMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.bot = MagicMock()
    callback.bot.delete_message = AsyncMock()
    callback.message = MagicMock()
    callback.message.chat.id = 12345
    callback.message.delete = AsyncMock()

    state = AsyncMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={"menu_msg_id": 100, "prompt_msg_id": 101})
    state.clear = AsyncMock()

    await process_dedinside_cancel(callback, state)

    callback.answer.assert_called_once()
    state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_process_count_selection():
    """Тест выбора 5 повторов."""
    callback = MagicMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.data = "dedinside_count_5"
    callback.bot = MagicMock()
    callback.bot.send_message = AsyncMock(return_value=MagicMock(message_id=200))
    callback.message = MagicMock()
    callback.message.chat.id = 12345

    state = AsyncMock(spec=FSMContext)
    state.set_state = AsyncMock()
    state.update_data = AsyncMock()

    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Prompt Text 5")

    await process_count_selection(callback, state, i18n)

    callback.answer.assert_called_once()
    state.set_state.assert_called_once_with(DedinsideStates.waiting_for_message)
    state.update_data.assert_called_once_with(count=5, prompt_msg_id=200)


@pytest.mark.asyncio
async def test_process_non_text_message():
    """Тест ответа на отправку файла/фото вместо текста."""
    message = MagicMock(spec=Message)
    message.answer = AsyncMock()

    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Text Only Warning")

    await process_non_text_message(message, i18n)

    message.answer.assert_called_once_with("Text Only Warning")


@pytest.mark.asyncio
async def test_process_spam_text_message():
    """Тест цикла отправки и удаления сообщений 5 раз."""
    message = MagicMock()
    message.text = "Hello Spam"
    message.chat.id = 12345
    message.bot = MagicMock()
    message.bot.delete_message = AsyncMock()
    message.bot.send_message = AsyncMock(return_value=MagicMock(message_id=500))
    message.delete = AsyncMock()

    state = AsyncMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={"count": 5, "menu_msg_id": 100, "prompt_msg_id": 101})
    state.set_state = AsyncMock()
    state.clear = AsyncMock()

    i18n = MagicMock(spec=I18nContext)

    with patch("asyncio.sleep", new=AsyncMock()):
        await process_spam_text_message(message, state, i18n)

    assert message.bot.send_message.call_count == 5
    state.clear.assert_called_once()

