from aiogram import Router
from filters.is_admin import IsAdmin
from .panel import router as panel_router
from .users import router as users_router
from .mailing import router as mailing_router
from .stats import router as stats_router
from .tickets import router as tickets_router
from .texts import router as texts_router

# Объединяющий роутер для административной зоны
router = Router(name="admin_main")

# Применяем фильтр IsAdmin глобально ко всем хендлерам внутри этого роутера
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

router.include_routers(
    panel_router,
    users_router,
    mailing_router,
    stats_router,
    tickets_router,
    texts_router
)

