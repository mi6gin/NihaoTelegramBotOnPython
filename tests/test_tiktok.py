import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram_i18n import I18nContext

from utils.tiktok_parser import TikTokParser
from commands.tiktok.handlers import (
    format_user_caption,
    cmd_mtiktok,
    cmd_ptiktok,
    show_tiktok_account_menu,
    tiktok_unbind_yes,
)
from commands.tiktok.states import TikTokStates
from database.models.user import User


def test_tiktok_url_regex_extraction():
    """Тест регулярного выражения извлечения ссылок TikTok."""
    sample_text = "Смотри это видео: https://vt.tiktok.com/ZSC6gkCG4/ оно супер!"
    extracted = TikTokParser.extract_url_from_text(sample_text)
    assert extracted == "https://vt.tiktok.com/ZSC6gkCG4/"


def test_format_user_caption():
    """Тест форматирования подписи к видео с жирным юзернеймом и кликабельной ссылкой <TikTok>."""
    user = User(telegram_id=123, username="testuser", first_name="Test")
    url = "https://vt.tiktok.com/ZSC6gkCG4/"
    caption = format_user_caption(user, url)
    assert "<b>@testuser</b>" in caption
    assert f'<a href="{url}">Ссылка на TikTok</a>' in caption


@pytest.mark.asyncio
async def test_cmd_mtiktok():
    """Тест старта микро-меню /Mtiktok."""
    message = MagicMock(spec=Message)
    message.answer = AsyncMock(return_value=MagicMock(message_id=500))
    state = AsyncMock(spec=FSMContext)
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(side_effect=lambda k, **kw: str(k))

    await cmd_mtiktok(message, state, i18n)

    message.answer.assert_called_once()
    state.set_state.assert_called_once_with(TikTokStates.waiting_for_audio_link)


@pytest.mark.asyncio
async def test_cmd_ptiktok():
    """Тест старта микро-меню /Ptiktok."""
    message = MagicMock(spec=Message)
    message.answer = AsyncMock(return_value=MagicMock(message_id=501))
    state = AsyncMock(spec=FSMContext)
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(side_effect=lambda k, **kw: str(k))

    await cmd_ptiktok(message, state, i18n)

    message.answer.assert_called_once()
    state.set_state.assert_called_once_with(TikTokStates.waiting_for_photo_link)


@pytest.mark.asyncio
async def test_show_tiktok_account_menu():
    """Тест показа экрана 1.1 Аккаунт TikTok."""
    callback = MagicMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    state = AsyncMock(spec=FSMContext)
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(side_effect=lambda k, **kw: f"{k} {kw.get('username', '')}")
    db_user = User(telegram_id=123, username="testuser", first_name="Test", tiktok_username="mytiktok")

    await show_tiktok_account_menu(callback, db_user, i18n, state)

    callback.answer.assert_called_once()
    state.clear.assert_called_once()
    callback.message.edit_text.assert_called_once()
    assert "mytiktok" in callback.message.edit_text.call_args[1]["text"]


@pytest.mark.asyncio
async def test_auto_download_tiktok_link_signature(db_session):
    """Тест вызова auto_download_tiktok_link с переданной сессией СУБД."""
    from commands.tiktok.handlers import auto_download_tiktok_link
    message = MagicMock(spec=Message)
    message.text = "https://www.tiktok.com/@user/video/732918239103847293"
    message.chat = MagicMock(id=12345)
    message.delete = AsyncMock()
    message.answer = AsyncMock(return_value=MagicMock(message_id=999))
    message.bot = MagicMock()
    message.bot.edit_message_text = AsyncMock()
    message.bot.send_chat_action = AsyncMock()
    message.answer_video = AsyncMock()

    db_user = User(telegram_id=123, username="testuser", first_name="Test")
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(side_effect=lambda k, **kw: str(k))

    with patch("utils.tiktok_parser.TikTokParser.get_post_info", new_callable=AsyncMock) as mock_info, \
         patch("utils.tiktok_parser.TikTokParser.download_video", new_callable=AsyncMock) as mock_down:
        mock_info.return_value = {"type": "video", "resolved_url": message.text, "title": "Test Title"}
        mock_down.return_value = None

        await auto_download_tiktok_link(message, db_user, db_session, i18n)
        message.answer.assert_called()

