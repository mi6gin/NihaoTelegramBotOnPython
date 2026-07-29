from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.support import SupportService
from database.models.user import User
from database.repository.ticket_repo import TicketRepository
from database.repository.user_repo import UserRepository
from domain.support import InvalidTicketMessage
from keyboards.inline.cancel import get_cancel_inline_keyboard
from keyboards.inline.user_menu import get_user_menu_keyboard
from filters.is_private import IsPrivate
from filters.is_admin import IsAdmin
from utils.logger import logger


class SupportStates(StatesGroup):
    """
    Состояния FSM для отправки обращения в поддержку.
    """
    waiting_for_ticket_message = State()


router = Router(name="user_support")
support_service = SupportService(TicketRepository(), UserRepository())


@router.callback_query(F.data.startswith("user_support"))
async def start_support_ticket(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Запускает процесс создания тикета поддержки (FSM) с заменой текста сообщения.
    """
    await callback.answer()
    
    prompt_msg = await callback.message.edit_text(
        i18n.get("support-prompt"),
        reply_markup=get_cancel_inline_keyboard(i18n, callback_data="cancel_support")
    )
    
    await state.set_state(SupportStates.waiting_for_ticket_message)
    await state.update_data(prompt_msg_id=prompt_msg.message_id)


@router.callback_query(F.data == "cancel_support")
async def process_cancel_support(callback: CallbackQuery, state: FSMContext, db_user: User, i18n: I18nContext):
    """
    Обработчик клика по инлайн-кнопке отмены при создании тикета.
    Возвращает пользователя в главное меню.
    """
    await callback.answer()
    await state.clear()
    
    is_admin_user = await IsAdmin()(callback, db_user)
    await callback.message.edit_text(
        i18n.get("menu-title"),
        reply_markup=get_user_menu_keyboard(i18n, is_admin=is_admin_user)
    )


@router.message(SupportStates.waiting_for_ticket_message, IsPrivate())
async def process_ticket_message(
    message: Message, 
    state: FSMContext, 
    session: AsyncSession, 
    db_user: User,
    i18n: I18nContext
):
    """
    Обрабатывает ввод сообщения для поддержки. Создает тикет в БД.
    """
    try:
        ticket_text = message.text.strip()
        ticket, admins = await support_service.create_ticket(
            session,
            db_user.telegram_id,
            ticket_text,
        )
    except InvalidTicketMessage:
        await message.answer(i18n.get("err-ticket-length"))
        return

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    if prompt_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_msg_id)
        except Exception:
            pass

    await state.clear()
    logger.info(f"User {db_user.telegram_id} created support ticket #{ticket.id}")

    for admin in admins:
        try:
            admin_locale = admin.language or "ru"
            builder = InlineKeyboardBuilder()
            builder.button(
                text=i18n.get("btn-ticket-reply", locale=admin_locale),
                callback_data=f"admin_alert_reply_{ticket.id}"
            )
            builder.button(
                text=i18n.get("btn-ticket-close-no-reply", locale=admin_locale),
                callback_data=f"admin_alert_close_{ticket.id}"
            )
            builder.adjust(1)
            
            alert_text = i18n.get(
                "admin-ticket-notification-alert",
                locale=admin_locale,
                id=str(ticket.id),
                name=db_user.first_name,
                username=db_user.username or i18n.get("profile-username-empty", locale=admin_locale),
                message=ticket_text
            )
            
            await message.bot.send_message(
                chat_id=admin.telegram_id,
                text=alert_text,
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            logger.warning(f"Failed to send alert to admin {admin.telegram_id}: {e}")

    is_admin_user = await IsAdmin()(message, db_user)
    await message.answer(
        i18n.get("support-success", id=str(ticket.id)),
        reply_markup=get_user_menu_keyboard(i18n, is_admin=is_admin_user)
    )
