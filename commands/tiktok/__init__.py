from aiogram import Router
from .handlers import router as tiktok_router

router = Router(name="tiktok_module")
router.include_router(tiktok_router)
