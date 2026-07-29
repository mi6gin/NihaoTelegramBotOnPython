import asyncio
import socket
from collections.abc import Coroutine
from contextlib import suppress
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

from application.bot_commands import set_bot_commands
from application.lifecycle import schedule_midnight_restart
from config.settings import settings
from database.engine import AsyncSessionLocal, init_db
from database.fsm_storage import SQLAlchemyStorage
from middlewares.ban_mw import BanMiddleware
from middlewares.db_session_mw import DbSessionMiddleware
from middlewares.i18n_mw import i18n_middleware
from middlewares.logging_mw import LoggingMiddleware
from middlewares.menu_owner_mw import MenuOwnerMiddleware
from middlewares.throttling_mw import ThrottlingMiddleware
from routers import get_main_router
from utils.logger import logger
from utils.text_manager import text_manager


def create_bot() -> Bot:
    """Create the Telegram client configured for this application."""
    session = AiohttpSession()
    # Telegram connectivity is more reliable on hosts with broken IPv6 routes.
    session._connector_init["family"] = socket.AF_INET
    return Bot(
        token=settings.bot_token.get_secret_value(),
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    """Create the dispatcher and register application middleware and routers."""
    dispatcher = Dispatcher(storage=SQLAlchemyStorage(AsyncSessionLocal))
    dispatcher.update.outer_middleware(DbSessionMiddleware(AsyncSessionLocal))
    dispatcher.update.outer_middleware(BanMiddleware())
    i18n_middleware.setup(dispatcher)
    dispatcher.callback_query.middleware(MenuOwnerMiddleware())
    dispatcher.message.outer_middleware(ThrottlingMiddleware())
    dispatcher.message.outer_middleware(LoggingMiddleware())
    dispatcher.callback_query.outer_middleware(LoggingMiddleware())
    dispatcher.include_router(get_main_router())
    return dispatcher


def _start_background_task(
    coroutine: Coroutine[Any, Any, Any],
    *,
    name: str,
) -> asyncio.Task[Any]:
    task = asyncio.create_task(coroutine, name=name)

    def log_failure(completed_task: asyncio.Task[Any]) -> None:
        if completed_task.cancelled():
            return
        try:
            error = completed_task.exception()
        except (asyncio.CancelledError, SystemExit):
            return
        if error is not None:
            logger.error(
                "Фоновая задача %s завершилась с ошибкой",
                completed_task.get_name(),
                exc_info=(type(error), error, error.__traceback__),
            )

    task.add_done_callback(log_failure)
    return task


async def _cancel_tasks(tasks: list[asyncio.Task[Any]]) -> None:
    for task in tasks:
        if not task.done():
            task.cancel()
    for task in tasks:
        with suppress(asyncio.CancelledError, SystemExit):
            await task


async def run_bot() -> None:
    """Initialize dependencies, run polling, and release owned resources."""
    logger.info("Запуск бота Нихао-тян...")
    await init_db()
    async with AsyncSessionLocal() as session:
        await text_manager.load_cache(session)

    bot = create_bot()
    dispatcher = create_dispatcher()
    background_tasks: list[asyncio.Task[Any]] = []

    try:
        try:
            await bot.delete_webhook(
                drop_pending_updates=True,
                request_timeout=10,
            )
        except Exception as error:
            logger.warning(
                "Пропуск сброса вебхука из-за задержки сети: %s",
                error,
            )

        background_tasks = [
            _start_background_task(
                set_bot_commands(bot),
                name="register-bot-commands",
            ),
            _start_background_task(
                schedule_midnight_restart(),
                name="midnight-restart",
            ),
        ]
        await dispatcher.start_polling(bot)
    finally:
        await _cancel_tasks(background_tasks)
        await dispatcher.storage.close()
        await bot.session.close()
