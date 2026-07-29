"""Administrative Telegram presentation routes."""

from aiogram import Router

from filters.is_admin import IsAdmin
from .mailing import router as mailing_router
from .panel import router as panel_router
from .stats import router as stats_router
from .texts import router as texts_router
from .tickets import router as tickets_router
from .users import router as users_router


router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())
router.include_routers(
    panel_router,
    users_router,
    mailing_router,
    stats_router,
    tickets_router,
    texts_router,
)

__all__ = ["router"]
