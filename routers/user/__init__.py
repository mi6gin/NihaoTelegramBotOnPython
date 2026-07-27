from aiogram import Router
from .start import router as start_router
from .profile import router as profile_router
from .catalog import router as catalog_router
from .support import router as support_router
from .dedinside import router as dedinside_router

# Объединяющий роутер для пользовательской зоны
router = Router(name="user_main")

router.include_routers(
    start_router,
    profile_router,
    catalog_router,
    support_router,
    dedinside_router
)

