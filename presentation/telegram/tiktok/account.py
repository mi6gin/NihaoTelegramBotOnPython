"""TikTok account binding and profile handlers."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User
from database.repository.user_repo import UserRepository
from infrastructure.tiktok import TikTokParser
from presentation.telegram.tiktok.keyboards import (
    get_tiktok_account_menu_keyboard,
    get_tiktok_cancel_keyboard,
    get_tiktok_unbind_confirm_keyboard,
)
from presentation.telegram.tiktok.states import TikTokStates


router = Router(name="tiktok_account")


@router.callback_query(F.data.startswith("tiktok_account_menu"))
async def show_tiktok_account_menu(
    callback: CallbackQuery,
    db_user: User,
    i18n: I18nContext,
    state: FSMContext,
):
    """Show the linked TikTok account and its public statistics."""
    await state.clear()
    await callback.answer()

    if db_user.tiktok_username:
        stats = await TikTokParser.fetch_user_info(db_user.tiktok_username)
        if stats:
            text = i18n.get(
                "tiktok-account-stats-title",
                username=stats["username"],
                nickname=stats["nickname"],
                followers=f"{stats['followers']:,}".replace(",", " "),
                likes=f"{stats['likes']:,}".replace(",", " "),
                videos=f"{stats['videos']:,}".replace(",", " "),
                bio=stats["bio"] or "—",
            )
        else:
            text = i18n.get(
                "tiktok-account-active-text",
                username=db_user.tiktok_username,
            )
    else:
        text = i18n.get("tiktok-account-unlinked-text")

    await callback.message.edit_text(
        text=text,
        reply_markup=get_tiktok_account_menu_keyboard(
            db_user.tiktok_username,
            i18n,
        ),
    )


@router.callback_query(F.data == "tiktok_bind_username")
async def start_bind_username(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nContext,
):
    """Prompt the user for a TikTok username."""
    await callback.answer()
    await state.set_state(TikTokStates.waiting_for_username)
    prompt_msg = await callback.message.edit_text(
        i18n.get("tiktok-bind-prompt-msg"),
        reply_markup=get_tiktok_cancel_keyboard(
            i18n,
            callback_data="tiktok_account_menu",
        ),
    )
    await state.update_data(prompt_msg_id=prompt_msg.message_id)


@router.message(TikTokStates.waiting_for_username, F.text)
async def process_username_input(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: User,
    i18n: I18nContext,
):
    """Validate and save a TikTok username."""
    raw_username = message.text.strip().lstrip("@")
    if not 2 <= len(raw_username) <= 30:
        await message.answer(i18n.get("tiktok-err-invalid-username"))
        return

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    if prompt_msg_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=prompt_msg_id,
            )
        except Exception:
            pass

    try:
        await message.delete()
    except Exception:
        pass

    await UserRepository.set_tiktok_username(
        session,
        db_user.telegram_id,
        raw_username,
    )
    await state.clear()
    await message.answer(
        text=i18n.get("tiktok-bind-success-msg", username=raw_username),
        reply_markup=get_tiktok_account_menu_keyboard(raw_username, i18n),
    )


@router.callback_query(F.data == "tiktok_unbind_confirm")
async def tiktok_unbind_confirm(
    callback: CallbackQuery,
    db_user: User,
    i18n: I18nContext,
):
    """Ask for confirmation before unlinking an account."""
    await callback.answer()
    await callback.message.edit_text(
        i18n.get(
            "tiktok-unbind-confirm-msg",
            username=db_user.tiktok_username,
        ),
        reply_markup=get_tiktok_unbind_confirm_keyboard(i18n),
    )


@router.callback_query(F.data == "tiktok_unbind_yes")
async def tiktok_unbind_yes(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
    i18n: I18nContext,
):
    """Unlink the user's TikTok account."""
    await callback.answer(
        i18n.get("tiktok-unbind-alert"),
        show_alert=True,
    )
    await UserRepository.set_tiktok_username(
        session,
        db_user.telegram_id,
        None,
    )
    await callback.message.edit_text(
        text=i18n.get("tiktok-account-unlinked-text"),
        reply_markup=get_tiktok_account_menu_keyboard(None, i18n),
    )
