"""Animated Telegram status message used during long-running operations."""

import asyncio
from typing import Any

from aiogram_i18n import I18nContext


class AnimatedStatus:
    """Animate a localized status message until the operation completes."""

    def __init__(
        self,
        bot: Any,
        chat_id: int,
        message_id: int,
        base_key: str,
        link: str,
        i18n: I18nContext,
    ) -> None:
        self.bot = bot
        self.chat_id = chat_id
        self.message_id = message_id
        self.base_key = base_key
        self.link = link
        self.i18n = i18n
        self.task: asyncio.Task[None] | None = None
        self._running = False
        self._dot_count = 1

    async def _animate(self) -> None:
        while self._running:
            try:
                await self._render()
            except Exception:
                pass
            self._dot_count = (self._dot_count % 3) + 1
            await asyncio.sleep(0.6)

    async def _render(self) -> None:
        dots = "." * self._dot_count
        text = self.i18n.get(self.base_key, link=self.link, dots=dots)
        await self.bot.edit_message_text(
            chat_id=self.chat_id,
            message_id=self.message_id,
            text=text,
            disable_web_page_preview=True,
        )

    def start(self) -> None:
        self._running = True
        self.task = asyncio.create_task(self._animate())

    async def set_key(self, new_key: str) -> None:
        self.base_key = new_key
        try:
            await self._render()
        except Exception:
            pass

    async def stop(self) -> None:
        self._running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        try:
            await self.bot.delete_message(
                chat_id=self.chat_id,
                message_id=self.message_id,
            )
        except Exception:
            pass
