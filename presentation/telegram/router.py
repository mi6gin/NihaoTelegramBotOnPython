"""Composition root for Telegram presentation routes."""

from aiogram import Router

from presentation.telegram.admin import router as admin_router
from presentation.telegram.errors import router as error_router
from presentation.telegram.user import router as user_router


def get_main_router() -> Router:
    """Build the root router in handler-precedence order."""
    router = Router(name="root")
    router.include_routers(
        admin_router,
        user_router,
        error_router,
    )
    return router
