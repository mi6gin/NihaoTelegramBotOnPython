from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject
from aiogram_i18n import I18nContext


class MenuOwnerMiddleware(BaseMiddleware):
    """
    Прослойка безопасности: блокирует нажатия чужих инлайн-кнопок меню в группах и личке.
    Если callback_data заканчивается на ':owner_id' и кнопку нажимает чужой пользователь,
    выводит всплывающее уведомление и прерывает выполнение.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, CallbackQuery) and event.data and ":" in event.data:
            parts = event.data.split(":")
            last_part = parts[-1]
            if last_part.isdigit():
                owner_id = int(last_part)
                if event.from_user.id != owner_id:
                    i18n: I18nContext = data.get("i18n")
                    err_msg = (
                        i18n.get("err-not-menu-owner")
                        if i18n
                        else "⚠️ Это меню создано для другого пользователя. Введите /start чтобы открыть свое!"
                    )
                    await event.answer(err_msg, show_alert=True)
                    return None

        return await handler(event, data)
