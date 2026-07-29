import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from aiogram import Bot
from aiogram.types import CallbackQuery, Message, User as TgUser
from aiogram.fsm.context import FSMContext
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from presentation.telegram.admin.tickets import (
    view_open_tickets, 
    close_ticket_no_reply, 
    start_ticket_reply, 
    process_ticket_reply,
    start_alert_ticket_reply,
    cancel_alert_reply,
    close_alert_ticket_no_reply
)
from presentation.telegram.user.catalog import select_catalog_item
from database.models.ticket import Ticket
from database.models.user import User


@pytest.mark.asyncio
async def test_view_open_tickets_empty():
    """Тест просмотра тикетов администратором, когда тикетов нет."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "admin_tickets_view_0"
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    
    session = MagicMock(spec=AsyncSession)
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="No tickets")
    state = AsyncMock(spec=FSMContext)

    with patch("database.repository.ticket_repo.TicketRepository.get_all_open", return_value=[]):
        await view_open_tickets(callback, session, i18n, state)
        
        callback.answer.assert_called_once()
        state.clear.assert_called_once()
        callback.message.edit_text.assert_called_once_with("No tickets", reply_markup=ANY)


@pytest.mark.asyncio
async def test_view_open_tickets_success():
    """Тест просмотра тикетов администратором, когда они есть в системе."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "admin_tickets_view_0"
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    
    session = MagicMock(spec=AsyncSession)
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Ticket template")
    state = AsyncMock(spec=FSMContext)

    mock_ticket = MagicMock(spec=Ticket)
    mock_ticket.id = 4
    mock_ticket.status = "open"
    mock_ticket.user_id = 1234
    mock_ticket.message = "Need help"
    mock_ticket.created_at = MagicMock()
    mock_ticket.user = MagicMock()
    mock_ticket.user.first_name = "Alice"
    mock_ticket.user.username = "alice_test"

    with patch("database.repository.ticket_repo.TicketRepository.get_all_open", return_value=[mock_ticket]):
        await view_open_tickets(callback, session, i18n, state)
        
        callback.answer.assert_called_once()
        state.clear.assert_called_once()
        callback.message.edit_text.assert_called_once()


@pytest.mark.asyncio
async def test_close_ticket_no_reply():
    """Тест закрытия тикета без текстового ответа."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "admin_ticket_close_no_reply_4_0"
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    
    session = MagicMock(spec=AsyncSession)
    bot = AsyncMock(spec=Bot)
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Closed info")
    state = AsyncMock(spec=FSMContext)

    mock_ticket = MagicMock(spec=Ticket)
    mock_ticket.id = 4
    mock_ticket.user_id = 1234
    mock_ticket.user = MagicMock()
    mock_ticket.user.language = "ru"

    with patch("database.repository.ticket_repo.TicketRepository.get_by_id", return_value=mock_ticket), \
         patch("database.repository.ticket_repo.TicketRepository.close", return_value=True) as mock_close, \
         patch("database.repository.ticket_repo.TicketRepository.get_all_open", return_value=[]):
         
        await close_ticket_no_reply(callback, session, bot, i18n, state)
        
        mock_close.assert_called_once_with(session, 4)
        callback.answer.assert_called_once_with("Closed info", show_alert=True)
        bot.send_message.assert_called_once_with(chat_id=1234, text="Closed info")


@pytest.mark.asyncio
async def test_start_ticket_reply():
    """Тест начала процесса ответа на тикет (FSM)."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "admin_ticket_reply_4_0"
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.message_id = 55
    callback.message.edit_text = AsyncMock(return_value=callback.message)
    
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Reply prompt text")
    state = AsyncMock(spec=FSMContext)

    await start_ticket_reply(callback, i18n, state)
    
    callback.answer.assert_called_once()
    state.set_state.assert_called_once()
    state.update_data.assert_called_once_with(ticket_id=4, index=0, prompt_msg_id=55)


@pytest.mark.asyncio
async def test_process_ticket_reply_success():
    """Тест успешного процессинга и отправки ответа на тикет."""
    message = MagicMock(spec=Message)
    message.text = "Hello customer!"
    message.answer = AsyncMock()
    message.chat = MagicMock()
    message.chat.id = 777
    message.from_user = MagicMock(spec=TgUser)
    
    session = MagicMock(spec=AsyncSession)
    bot = AsyncMock(spec=Bot)
    
    state = AsyncMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={"ticket_id": 4, "index": 0, "prompt_msg_id": 55})

    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Notification template text")

    mock_ticket = MagicMock(spec=Ticket)
    mock_ticket.id = 4
    mock_ticket.user_id = 1234
    mock_ticket.user = MagicMock()
    mock_ticket.user.language = "en"

    with patch("database.repository.ticket_repo.TicketRepository.get_by_id", return_value=mock_ticket), \
         patch("database.repository.ticket_repo.TicketRepository.close", return_value=True) as mock_close, \
         patch("database.repository.ticket_repo.TicketRepository.get_all_open", return_value=[]):
         
        await process_ticket_reply(message, session, bot, state, i18n)
        
        state.clear.assert_called_once()
        bot.delete_message.assert_called_once_with(chat_id=777, message_id=55)
        mock_close.assert_called_once_with(session, 4)
        bot.send_message.assert_called_once_with(chat_id=1234, text="Notification template text")
        assert message.answer.call_count == 2
        calls = message.answer.call_args_list
        assert calls[0][0][0] == "Notification template text" # Первый вызов: инфо об отмене/закрытии
        assert calls[1][0][0] == "Notification template text" # Второй вызов: пустой список тикетов
        assert "reply_markup" in calls[1][1]


@pytest.mark.asyncio
async def test_select_catalog_theme():
    """Тест активации темы пользователем в каталоге."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "catalog_select_theme_sakura"
    callback.answer = AsyncMock()
    
    session = MagicMock(spec=AsyncSession)
    db_user = MagicMock(spec=User)
    db_user.telegram_id = 9876
    
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Sakura Style applied")

    with patch("database.repository.user_repo.UserRepository.set_selected_theme", return_value=True) as mock_set_theme:
        await select_catalog_item(callback, session, db_user, i18n)
        
        mock_set_theme.assert_called_once_with(session, 9876, "theme_sakura")
        callback.answer.assert_called_once_with("Sakura Style applied", show_alert=True)


@pytest.mark.asyncio
async def test_start_alert_ticket_reply():
    """Тест вызова быстрого ответа из алерта."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "admin_alert_reply_55"
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.message_id = 999
    callback.message.answer = AsyncMock()
    
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Prompt")
    state = AsyncMock(spec=FSMContext)
    
    await start_alert_ticket_reply(callback, i18n, state)
    
    callback.answer.assert_called_once()
    state.set_state.assert_called_once()
    state.update_data.assert_called_once_with(
        ticket_id=55,
        prompt_msg_id=ANY,
        is_alert=True,
        alert_msg_id=999
    )


@pytest.mark.asyncio
async def test_cancel_alert_reply():
    """Тест отмены быстрого ответа из алерта."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "cancel_alert_reply_55"
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.delete = AsyncMock()
    
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Cancelled")
    state = AsyncMock(spec=FSMContext)
    
    await cancel_alert_reply(callback, i18n, state)
    
    state.clear.assert_called_once()
    callback.answer.assert_called_once_with("Cancelled")
    callback.message.delete.assert_called_once()


@pytest.mark.asyncio
async def test_close_alert_ticket_no_reply():
    """Тест быстрого закрытия тикета без ответа из алерта."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "admin_alert_close_55"
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.text = "Alert Message Body"
    callback.message.edit_text = AsyncMock()
    
    session = MagicMock(spec=AsyncSession)
    bot = AsyncMock(spec=Bot)
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Notification info")
    state = AsyncMock(spec=FSMContext)
    
    mock_ticket = MagicMock(spec=Ticket)
    mock_ticket.id = 55
    mock_ticket.user_id = 777
    mock_ticket.user = MagicMock()
    mock_ticket.user.language = "ru"
    
    with patch("database.repository.ticket_repo.TicketRepository.get_by_id", return_value=mock_ticket), \
         patch("database.repository.ticket_repo.TicketRepository.close", return_value=True) as mock_close:
         
        await close_alert_ticket_no_reply(callback, session, bot, i18n, state)
        
        state.clear.assert_called_once()
        mock_close.assert_called_once_with(session, 55)
        callback.answer.assert_called_once_with("Notification info", show_alert=True)
        bot.send_message.assert_called_once_with(chat_id=777, text="Notification info")
        callback.message.edit_text.assert_called_once()


@pytest.mark.asyncio
async def test_process_ticket_reply_alert_success():
    """Тест успешного процессинга ответа, когда он был инициирован из алерта."""
    message = MagicMock(spec=Message)
    message.text = "Here is my support response"
    message.answer = AsyncMock()
    message.chat = MagicMock()
    message.chat.id = 1212
    
    session = MagicMock(spec=AsyncSession)
    bot = AsyncMock(spec=Bot)
    bot.delete_message = AsyncMock()
    bot.edit_message_text = AsyncMock()
    
    state = AsyncMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={
        "ticket_id": 55,
        "index": None,
        "prompt_msg_id": 888,
        "is_alert": True,
        "alert_msg_id": 999
    })
    
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(return_value="Reply successful template")
    
    mock_ticket = MagicMock(spec=Ticket)
    mock_ticket.id = 55
    mock_ticket.user_id = 777
    mock_ticket.user = MagicMock()
    mock_ticket.user.language = "ru"
    
    with patch("database.repository.ticket_repo.TicketRepository.get_by_id", return_value=mock_ticket), \
         patch("database.repository.ticket_repo.TicketRepository.close", return_value=True) as mock_close:
         
        await process_ticket_reply(message, session, bot, state, i18n)
        
        state.clear.assert_called_once()
        bot.delete_message.assert_called_once_with(chat_id=1212, message_id=888)
        mock_close.assert_called_once_with(session, 55)
        bot.send_message.assert_called_once_with(chat_id=777, text="Reply successful template")
        message.answer.assert_called_once_with("Reply successful template")
        bot.edit_message_text.assert_called_once_with(
            chat_id=1212,
            message_id=999,
            text="Reply successful template",
            reply_markup=None
        )
