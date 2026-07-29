import asyncio
import math
import time
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.repository.user_repo import UserRepository
from keyboards.inline.admin_panel import get_admin_panel_keyboard
from keyboards.inline.cancel import get_cancel_inline_keyboard
from filters.is_private import IsPrivate
from filters.is_admin import IsAdmin
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram_i18n import I18nContext
from utils.logger import logger
from database.models.user import User
from sqlalchemy import select

router = Router(name="admin_mailing")


class AdminMailingStates(StatesGroup):
    """
    Состояния FSM для проведения таргетированной рассылки.
    """
    # Ожидание выбора аудитории (в чек-листе)
    waiting_for_audience = State()
    # Ожидание ввода контента для рассылки
    waiting_for_content = State()


# Глобальный RAM-кэш пользователей для исключения лишних запросов к СУБД
# { "timestamp": float, "users": List[Dict] }
USERS_CACHE = {"timestamp": 0.0, "users": []}
CACHE_TTL = 60.0  # Время жизни кэша (в секундах)


async def get_cached_users(session: AsyncSession) -> list:
    """
    Возвращает облегченный список пользователей из кэша в оперативной памяти.
    Если кэш пуст или устарел, делает ровно один точечный запрос к БД.
    """
    now = time.time()
    if USERS_CACHE["users"] and (now - USERS_CACHE["timestamp"] < CACHE_TTL):
        return USERS_CACHE["users"]
        
    # Запрашиваем только необходимые поля, минуя тяжелые ORM-объекты
    query = (
        select(User.telegram_id, User.first_name, User.username)
        .where(User.telegram_id > 0)
        .order_by(User.registered_at.desc())
    )
    result = await session.execute(query)
    rows = result.all()
    
    users = []
    for row in rows:
        users.append({
            "telegram_id": row[0],
            "first_name": row[1],
            "username": row[2]
        })
        
    USERS_CACHE["users"] = users
    USERS_CACHE["timestamp"] = now
    return users


@router.callback_query(F.data == "admin_mailing", IsPrivate(), IsAdmin())
async def start_mailing_panel(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Панель выбора аудитории для начала рассылки.
    """
    await callback.answer()
    await state.clear()
    
    # Сбрасываем кэш при входе, чтобы список пользователей обновился
    USERS_CACHE["users"] = []
    USERS_CACHE["timestamp"] = 0.0
    
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.get("btn-mailing-target-all"), callback_data="mailing_target_all")
    builder.button(text=i18n.get("btn-mailing-target-filters"), callback_data="mailing_target_filters")
    builder.button(text=i18n.get("btn-mailing-target-list"), callback_data="mailing_target_list_0")
    builder.button(text=i18n.get("btn-admin-panel"), callback_data="admin_panel_entry")
    builder.adjust(1)
    
    await callback.message.edit_text(
        i18n.get("admin-mailing-target-prompt"),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "mailing_target_filters", IsPrivate(), IsAdmin())
async def show_filters_submenu(callback: CallbackQuery, i18n: I18nContext):
    """
    Подменю фильтров таргетинга (Язык / Стиль).
    """
    await callback.answer()
    
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.get("btn-mailing-filter-lang-ru"), callback_data="mailing_filter_lang_ru")
    builder.button(text=i18n.get("btn-mailing-filter-lang-en"), callback_data="mailing_filter_lang_en")
    builder.button(text=i18n.get("btn-mailing-filter-theme"), callback_data="mailing_filter_themes")
    builder.button(text=i18n.get("btn-back-to-menu"), callback_data="admin_mailing")
    builder.adjust(2, 1, 1)
    
    await callback.message.edit_text(
        i18n.get("admin-mailing-filters-prompt"),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "mailing_filter_themes", IsPrivate(), IsAdmin())
async def show_themes_submenu(callback: CallbackQuery, i18n: I18nContext):
    """
    Подменю выбора конкретного стиля оформления для таргетинга.
    """
    await callback.answer()
    
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.get("catalog-classic-title"), callback_data="mailing_filter_theme_theme_classic")
    builder.button(text=i18n.get("catalog-sakura-title"), callback_data="mailing_filter_theme_theme_sakura")
    builder.button(text=i18n.get("catalog-cyberpunk-title"), callback_data="mailing_filter_theme_theme_cyberpunk")
    builder.button(text=i18n.get("btn-back-to-menu"), callback_data="mailing_target_filters")
    builder.adjust(1)
    
    await callback.message.edit_text(
        i18n.get("admin-mailing-themes-prompt"),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("mailing_target_all"), IsPrivate(), IsAdmin())
@router.callback_query(F.data.startswith("mailing_filter_lang_"), IsPrivate(), IsAdmin())
@router.callback_query(F.data.startswith("mailing_filter_theme_"), IsPrivate(), IsAdmin())
async def process_audience_selection(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Обрабатывает выбор аудитории и переводит FSM в режим ожидания контента рассылки.
    """
    await callback.answer()
    
    data = callback.data
    target_filter = ""
    target_name = ""
    
    if data == "mailing_target_all":
        target_filter = "all"
        target_name = i18n.get("btn-mailing-target-all")
    elif data.startswith("mailing_filter_lang_"):
        lang = data.replace("mailing_filter_lang_", "")
        target_filter = f"lang_{lang}"
        target_name = i18n.get("btn-mailing-filter-lang-ru") if lang == "ru" else i18n.get("btn-mailing-filter-lang-en")
    elif data.startswith("mailing_filter_theme_"):
        theme_id = data.replace("mailing_filter_theme_", "")
        target_filter = f"theme_{theme_id}"
        theme_map = {
            "theme_classic": "catalog-classic-title",
            "theme_sakura": "catalog-sakura-title",
            "theme_cyberpunk": "catalog-cyberpunk-title"
        }
        target_name = i18n.get(theme_map.get(theme_id, "catalog-classic-title"))

    prompt_msg = await callback.message.edit_text(
        i18n.get("admin-mailing-prompt", target=target_name),
        reply_markup=get_cancel_inline_keyboard(i18n, callback_data="cancel_admin_mailing")
    )
    
    await state.set_state(AdminMailingStates.waiting_for_content)
    await state.update_data(
        target_filter=target_filter,
        target_name=target_name,
        prompt_msg_id=prompt_msg.message_id
    )


@router.callback_query(F.data.startswith("mailing_target_list_"), IsPrivate(), IsAdmin())
async def view_target_list(
    callback: CallbackQuery, 
    session: AsyncSession, 
    state: FSMContext, 
    i18n: I18nContext,
    page: int = None,
    selected_ids: list = None
):
    """
    Интерактивный чек-лист пользователей с постраничной навигацией (пагинация).
    Использует кэш в оперативной памяти для исключения повторных запросов к СУБД.
    """
    await callback.answer()
    
    # Определяем страницу
    if page is None:
        try:
            page = int(callback.data.replace("mailing_target_list_", ""))
        except ValueError:
            page = 0
            
    # Получаем выбранные ID из стейта, если не переданы
    if selected_ids is None:
        state_data = await state.get_data()
        selected_ids = state_data.get("selected_ids", [])
    
    # Загружаем пользователей из кэша
    users = await get_cached_users(session)
    
    if not users:
        builder = InlineKeyboardBuilder()
        builder.button(text=i18n.get("btn-admin-panel"), callback_data="admin_panel_entry")
        await callback.message.edit_text(i18n.get("err-no-users"), reply_markup=builder.as_markup())
        return

    # Пагинация (по 7 пользователей на страницу)
    per_page = 7
    total_pages = math.ceil(len(users) / per_page)
    if page < 0:
        page = 0
    elif page >= total_pages:
        page = total_pages - 1
        
    page_users = users[page * per_page : (page + 1) * per_page]
    
    builder = InlineKeyboardBuilder()
    
    # 1. Выводим список пользователей
    for u in page_users:
        tg_id = u["telegram_id"]
        is_selected = tg_id in selected_ids
        prefix = "✅ " if is_selected else "⬜️ "
        username_str = f" @{u['username']}" if u["username"] else ""
        btn_text = f"{prefix}{u['first_name']}{username_str}"
        builder.button(text=btn_text, callback_data=f"mailing_list_toggle_{tg_id}_{page}")
        
    # 2. Ряд кнопок пагинации страницы
    pagination_row = 0
    if page > 0:
        builder.button(text="⬅️", callback_data=f"mailing_target_list_{page-1}")
        pagination_row += 1
        
    builder.button(text=f"{page+1}/{total_pages}", callback_data="noop")
    pagination_row += 1
    
    if page < total_pages - 1:
        builder.button(text="➡️", callback_data=f"mailing_target_list_{page+1}")
        pagination_row += 1

    # 3. Кнопка отправки рассылки выбранным
    builder.button(text=i18n.get("btn-mailing-list-send", count=str(len(selected_ids))), callback_data="mailing_list_confirm")
    
    # 4. Кнопка Назад
    builder.button(text=i18n.get("btn-back-to-menu"), callback_data="admin_mailing")
    
    # Разметка клавиатуры
    adjust_pattern = [1] * len(page_users)
    adjust_pattern.append(pagination_row)
    adjust_pattern.append(1)
    adjust_pattern.append(1)
    
    builder.adjust(*adjust_pattern)
    
    await callback.message.edit_text(
        i18n.get("admin-mailing-list-prompt", count=str(len(selected_ids))),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("mailing_list_toggle_"), IsPrivate(), IsAdmin())
async def toggle_list_user(
    callback: CallbackQuery, 
    session: AsyncSession, 
    state: FSMContext, 
    i18n: I18nContext
):
    """
    Выбирает или снимает выделение с пользователя в списке рассылки.
    """
    # callback_data: mailing_list_toggle_{user_id}_{current_page}
    parts = callback.data.split("_")
    user_id = int(parts[3])
    page = int(parts[4])
    
    state_data = await state.get_data()
    selected_ids = state_data.get("selected_ids", [])
    
    if user_id in selected_ids:
        selected_ids.remove(user_id)
    else:
        selected_ids.append(user_id)
        
    await state.update_data(selected_ids=selected_ids)
    
    # Сразу обновляем экран списка без повторного запроса стейта
    await view_target_list(callback, session, state, i18n, page, selected_ids=selected_ids)


@router.callback_query(F.data == "mailing_list_confirm", IsPrivate(), IsAdmin())
async def confirm_list_mailing(
    callback: CallbackQuery, 
    state: FSMContext, 
    i18n: I18nContext
):
    """
    Переходит к вводу сообщения для выбранного списка ID.
    """
    state_data = await state.get_data()
    selected_ids = state_data.get("selected_ids", [])
    
    if not selected_ids:
        await callback.answer("Выберите хотя бы одного получателя!", show_alert=True)
        return
        
    await callback.answer()
    
    target_name = f"Выборочно ({len(selected_ids)} чел.)"
    
    prompt_msg = await callback.message.edit_text(
        i18n.get("admin-mailing-prompt", target=target_name),
        reply_markup=get_cancel_inline_keyboard(i18n, callback_data="cancel_admin_mailing")
    )
    
    await state.set_state(AdminMailingStates.waiting_for_content)
    await state.update_data(
        target_filter="list",
        target_name=target_name,
        prompt_msg_id=prompt_msg.message_id
    )


@router.callback_query(F.data == "cancel_admin_mailing", IsPrivate(), IsAdmin())
async def process_cancel_mailing(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    """
    Отмена рассылки при клике на инлайн-кнопку. Возвращает в меню рассылок.
    """
    await callback.answer()
    await state.clear()
    
    # Сбрасываем кэш
    USERS_CACHE["users"] = []
    USERS_CACHE["timestamp"] = 0.0
    
    await start_mailing_panel(callback, state, i18n)


@router.message(AdminMailingStates.waiting_for_content, IsPrivate(), IsAdmin())
async def process_mailing_content(
    message: Message, 
    state: FSMContext, 
    session: AsyncSession, 
    bot: Bot,
    i18n: I18nContext
):
    """
    Получает контент рассылки, совершает рассылку по списку пользователей из БД на основе фильтров.
    """
    data = await state.get_data()
    target_filter = data.get("target_filter", "all")
    selected_ids = data.get("selected_ids", [])
    prompt_msg_id = data.get("prompt_msg_id")
    
    await state.clear()

    # Сбрасываем кэш
    USERS_CACHE["users"] = []
    USERS_CACHE["timestamp"] = 0.0

    # Удаляем сообщение-подсказку с инлайн-кнопкой отмены
    if prompt_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prompt_msg_id)
        except Exception:
            pass

    # 1. Загружаем отфильтрованную аудиторию
    if target_filter == "all":
        query = select(User).where(User.telegram_id > 0)
    elif target_filter == "lang_ru":
        query = select(User).where(User.telegram_id > 0, User.language == "ru")
    elif target_filter == "lang_en":
        query = select(User).where(User.telegram_id > 0, User.language == "en")
    elif target_filter.startswith("theme_"):
        theme_id = target_filter.replace("theme_", "")
        query = select(User).where(User.telegram_id > 0, User.selected_theme == theme_id)
    elif target_filter == "list":
        query = select(User).where(User.telegram_id.in_(selected_ids))
    else:
        query = select(User).where(User.telegram_id > 0)

    result = await session.execute(query)
    users = list(result.scalars().all())
    
    if not users:
        await message.answer(i18n.get("err-no-users"))
        return

    status_msg = await message.answer(i18n.get("admin-mailing-sending"))

    success_count = 0
    fail_count = 0

    for user in users:
        if user.is_banned:
            continue
            
        try:
            await message.copy_to(chat_id=user.telegram_id)
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.debug(f"Failed to send mailing message to {user.telegram_id}: {e}")
            fail_count += 1

    await status_msg.delete()
    
    await message.answer(
        i18n.get(
            "admin-mailing-success",
            success=str(success_count),
            failed=str(fail_count)
        ),
        reply_markup=get_admin_panel_keyboard(i18n)
    )
