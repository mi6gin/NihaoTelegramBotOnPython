import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config.settings import settings
from database.engine import init_db, AsyncSessionLocal
from middlewares.db_session_mw import DbSessionMiddleware
from middlewares.ban_mw import BanMiddleware
from middlewares.throttling_mw import ThrottlingMiddleware
from middlewares.logging_mw import LoggingMiddleware
from middlewares.i18n_mw import i18n_middleware
from routers import get_main_router
from utils.logger import logger


async def set_bot_commands(bot: Bot):
    """
    Устанавливает локализованные меню команд в интерфейсе Telegram.
    """
    commands_en = [
        BotCommand(command="start", description="Launch the bot / Menu 🌸"),
        BotCommand(command="help", description="Show help info ℹ️"),
        BotCommand(command="about", description="About Nihao-chan ✨"),
        BotCommand(command="dedinside", description="Special dedinside mode 🖤"),
        BotCommand(command="mtiktok", description="Download TikTok audio MP3 🎵"),
        BotCommand(command="ptiktok", description="Download TikTok slideshow 🖼️"),
    ]
    
    commands_ru = [
        BotCommand(command="start", description="Запустить бота / Меню 🌸"),
        BotCommand(command="help", description="Показать справку ℹ️"),
        BotCommand(command="about", description="О Нихао-тян ✨"),
        BotCommand(command="dedinside", description="Особый режим dedinside 🖤"),
        BotCommand(command="mtiktok", description="Скачать аудио из TikTok 🎵"),
        BotCommand(command="ptiktok", description="Скачать слайдшоу из TikTok 🖼️"),
    ]
    
    for attempt in range(1, 4):
        try:
            # Сначала регистрируем основное меню
            await bot.set_my_commands(commands_ru, request_timeout=30)
            # Затем локализованные версии
            try:
                await bot.set_my_commands(commands_ru, language_code="ru", request_timeout=30)
                await bot.set_my_commands(commands_en, language_code="en", request_timeout=30)
            except Exception as loc_e:
                logger.debug(f"Локализованные меню пропущены: {loc_e}")
                
            logger.info("Команды меню бота успешно зарегистрированы.")
            break
        except Exception as e:
            if attempt == 3:
                logger.warning(f"Не удалось установить меню команд (проблемы сети Telegram API): {e}")
            else:
                await asyncio.sleep(3)


async def schedule_midnight_restart():
    """
    Фоновая задача, которая вычисляет время до следующей полуночи (00:00)
    и мягко завершает процесс бота.
    Благодаря Docker restart policy (restart: unless-stopped),
    бот автоматически поднимется заново.
    """
    import datetime
    import sys
    
    now = datetime.datetime.now()
    tomorrow = now + datetime.timedelta(days=1)
    midnight = datetime.datetime(
        year=tomorrow.year,
        month=tomorrow.month,
        day=tomorrow.day,
        hour=0,
        minute=0,
        second=0
    )
    seconds_to_wait = (midnight - now).total_seconds()
    
    logger.info(f"Запланирован автоперезапуск бота в 00:00. До перезапуска осталось {seconds_to_wait:.1f} сек.")
    
    await asyncio.sleep(seconds_to_wait)
    
    logger.info("Время 00:00. Инициируем мягкий перезапуск бота...")
    await asyncio.sleep(1)
    sys.exit(0)


async def main():
    """
    Основная функция запуска бота Нихао-тян.
    """
    logger.info("Запуск бота Нихао-тян...")

    # 1. Инициализация базы данных (создание таблиц)
    await init_db()

    # Загружаем динамические тексты из СУБД в кэш RAM
    from utils.text_manager import text_manager
    async with AsyncSessionLocal() as session:
        await text_manager.load_cache(session)

    # 2. Инициализация бота с явным таймаутом сетевой сессии AiohttpSession
    from aiogram.client.session.aiohttp import AiohttpSession
    session = AiohttpSession(timeout=30.0)

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    from database.fsm_storage import SQLAlchemyStorage
    storage = SQLAlchemyStorage(AsyncSessionLocal)
    dp = Dispatcher(storage=storage)

    # 3. Регистрация Middleware (прослоек).
    dp.update.outer_middleware(DbSessionMiddleware(AsyncSessionLocal))
    dp.update.outer_middleware(BanMiddleware())
    i18n_middleware.setup(dp)
    dp.message.outer_middleware(ThrottlingMiddleware())
    dp.message.outer_middleware(LoggingMiddleware())
    dp.callback_query.outer_middleware(LoggingMiddleware())

    # 4. Подключение общего роутера хендлеров
    dp.include_router(get_main_router())

    # 5. Сброс вебхука с защитой по таймауту
    try:
        await bot.delete_webhook(drop_pending_updates=True, request_timeout=10)
    except Exception as e:
        logger.warning(f"Пропуск сброса вебхука из-за задержки сети: {e}")

    # 6. Фоновый запуск установки меню команд и планировщика
    asyncio.create_task(set_bot_commands(bot))
    asyncio.create_task(schedule_midnight_restart())

    # 7. Запуск polling-а
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Критическая ошибка при работе бота: {e}", exc_info=True)
    finally:
        # Корректное закрытие сессий при завершении
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот Нихао-тян остановлен пользователем.")
        sys.exit(0)
