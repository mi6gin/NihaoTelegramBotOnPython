from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database.repository.user_repo import UserRepository
from keyboards.inline.admin_panel import get_admin_panel_keyboard
from keyboards.inline.cancel import get_cancel_inline_keyboard
from filters.is_private import IsPrivate
from filters.is_admin import IsAdmin
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram_i18n import I18nContext
from utils.logger import logger

router = Router(name="admin_users")


class AdminUserManageStates(StatesGroup):
    """
    Состояния FSM для управления пользователями администратором.
    """
    # Ожидание ввода Telegram ID целевого пользователя
    waiting_for_target_id = State()


@router.callback_query(F.data == "admin_users_manage", IsPrivate(), IsAdmin())
async def start_manage_users(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Запускает FSM для смены статуса бана пользователя.
    """
    await callback.answer()
    
    prompt_msg = await callback.message.edit_text(
        i18n.get("admin-users-prompt"),
        reply_markup=get_cancel_inline_keyboard(i18n, callback_data="cancel_admin_users_manage")
    )
    
    await state.set_state(AdminUserManageStates.waiting_for_target_id)
    await state.update_data(prompt_msg_id=prompt_msg.message_id)


@router.callback_query(F.data == "cancel_admin_users_manage", IsPrivate(), IsAdmin())
async def process_cancel_manage_users(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Отмена управления пользователями при клике на инлайн-кнопку.
    Возвращает в админ-панель.
    """
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text(
        i18n.get("admin-panel-title"),
        reply_markup=get_admin_panel_keyboard(i18n)
    )


@router.message(AdminUserManageStates.waiting_for_target_id, IsPrivate(), IsAdmin())
async def process_ban_unban(
    message: Message, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: I18nContext
):
    """
    Принимает ID пользователя, находит его в БД и инвертирует его флаг бана (is_banned).
    """
    # Удаляем сообщение-подсказку с инлайн-кнопкой отмены
    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    if prompt_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_msg_id)
        except Exception:
            pass

    input_text = message.text.strip()
    
    # Валидируем ввод Telegram ID (должно быть числом)
    if not input_text.isdigit():
        await message.answer(i18n.get("err-invalid-tg-id"))
        return
        
    target_id = int(input_text)
    
    # Предотвращаем самоблокировку
    if target_id == message.from_user.id:
        await message.answer(i18n.get("err-self-ban"))
        await state.clear()
        await message.answer(i18n.get("admin-panel-title"), reply_markup=get_admin_panel_keyboard(i18n))
        return
 
    # Получаем пользователя из БД
    target_user = await UserRepository.get_by_id(session, target_id)
    
    if not target_user:
        await message.answer(i18n.get("err-user-not-found", id=str(target_id)))
        await state.clear()
        await message.answer(i18n.get("admin-panel-title"), reply_markup=get_admin_panel_keyboard(i18n))
        return

    # Предотвращаем бан других админов
    if target_user.role == "admin":
        await message.answer(i18n.get("err-ban-admin"))
        await state.clear()
        await message.answer(i18n.get("admin-panel-title"), reply_markup=get_admin_panel_keyboard(i18n))
        return

    # Переключаем статус бана
    new_ban_status = not target_user.is_banned
    await UserRepository.set_ban_status(session, target_id, new_ban_status)
    
    status_text = i18n.get("admin-users-banned") if new_ban_status else i18n.get("admin-users-unbanned")
    logger.warning(f"Admin {message.from_user.id} changed ban status of user {target_id} to {new_ban_status}")
    
    await state.clear()
    await message.answer(
        i18n.get(
            "admin-users-status-changed",
            name=target_user.first_name,
            id=str(target_id),
            status=status_text
        ),
        reply_markup=get_admin_panel_keyboard(i18n)
    )
