from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.repository.user_repo import UserRepository
from database.repository.ticket_repo import TicketRepository
from filters.is_private import IsPrivate
from filters.is_admin import IsAdmin
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram_i18n import I18nContext

router = Router(name="admin_stats")


@router.callback_query(F.data == "admin_stats", IsPrivate(), IsAdmin())
async def show_stats(callback: CallbackQuery, session: AsyncSession, i18n: I18nContext):
    """
    Отображает административную статистику по базе данных бота.
    """
    await callback.answer()
    
    # Считаем количество записей в таблицах
    total_users = await UserRepository.get_total_count(session)
    banned_users = await UserRepository.get_banned_count(session)
    open_tickets = await TicketRepository.get_open_count(session)
    
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.get("btn-admin-panel"), callback_data="admin_panel_entry")
    
    await callback.message.edit_text(
        i18n.get(
            "admin-stats-title",
            total=str(total_users),
            banned=str(banned_users),
            tickets=str(open_tickets)
        ),
        reply_markup=builder.as_markup()
    )
