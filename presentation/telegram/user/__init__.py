"""User-facing Telegram presentation routes."""

from aiogram import Router

from .catalog import router as catalog_router
from .dedinside import router as dedinside_router
from .favorites import router as favorites_router
from .inline_mode import router as inline_mode_router
from .profile import router as profile_router
from .start import router as start_router
from .support import router as support_router
from presentation.telegram.tiktok import router as tiktok_router


router = Router(name="user")
router.include_routers(
    start_router,
    profile_router,
    catalog_router,
    support_router,
    dedinside_router,
    tiktok_router,
    favorites_router,
    inline_mode_router,
)

__all__ = ["router"]
