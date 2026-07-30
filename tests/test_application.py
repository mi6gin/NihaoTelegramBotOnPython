import datetime
from unittest.mock import AsyncMock, call, patch
from zoneinfo import ZoneInfo

import pytest

from application.bot_commands import COMMANDS_BY_LOCALE, set_bot_commands
from application.lifecycle import seconds_until_next_midnight


def test_seconds_until_next_midnight() -> None:
    now = datetime.datetime(2026, 7, 27, 23, 59, 50)

    assert seconds_until_next_midnight(now) == 10


def test_seconds_until_next_midnight_across_dst_change() -> None:
    now = datetime.datetime(
        2026,
        3,
        29,
        0,
        0,
        tzinfo=ZoneInfo("Europe/Berlin"),
    )

    assert seconds_until_next_midnight(now) == 23 * 60 * 60


@pytest.mark.asyncio
async def test_set_bot_commands_registers_default_and_locales() -> None:
    bot = AsyncMock()

    await set_bot_commands(bot)

    assert bot.set_my_commands.await_args_list == [
        call(COMMANDS_BY_LOCALE["ru"], request_timeout=30),
        call(
            COMMANDS_BY_LOCALE["ru"],
            language_code="ru",
            request_timeout=30,
        ),
        call(
            COMMANDS_BY_LOCALE["en"],
            language_code="en",
            request_timeout=30,
        ),
    ]


@pytest.mark.asyncio
async def test_set_bot_commands_retries_default_registration() -> None:
    bot = AsyncMock()
    bot.set_my_commands.side_effect = [
        RuntimeError("temporary failure"),
        None,
        None,
        None,
    ]

    with patch("application.bot_commands.asyncio.sleep", new=AsyncMock()) as sleep:
        await set_bot_commands(bot)

    sleep.assert_awaited_once_with(3)
