from aiogram import Router
from commands import router as commands_router
from .admin import router as admin_router
from .errors.error_handler import router as error_router


def get_main_router() -> Router:
    """
    Создает и возвращает главный роутер, объединяющий все маршруты бота.
    """
    main_router = Router(name="root_main")
    
    # Рекомендуется подключать админский роутер первым,
    # чтобы избежать ложных срабатываний общих пользовательских фильтров
    main_router.include_routers(
        admin_router,
        commands_router,
        error_router
    )
    
    return main_router
