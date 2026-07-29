from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery
from aiogram_i18n import I18nContext


class IsMenuOwnerFilter(BaseFilter):
    """
    Фильтр, проверяющий, является ли пользователь, нажавший на инлайн-кнопку,
    владельцем меню (чья команда /start вывела это меню).
    Если к кнопке привязан ID другого пользователя, показывает всплывающее предупреждение.
    """
    async def __call__(self, callback: CallbackQuery, i18n: I18nContext) -> bool:
        if not callback.data or ":" not in callback.data:
            return True

        parts = callback.data.split(":")
        last_part = parts[-1]

        if last_part.isdigit():
            owner_id = int(last_part)
            if callback.from_user.id != owner_id:
                err_msg = (
                    i18n.get("err-not-menu-owner")
                    if i18n
                    else "⚠️ Это меню создано для другого пользователя. Введите /start чтобы открыть свое!"
                )
                await callback.answer(err_msg, show_alert=True)
                return False

        return True
