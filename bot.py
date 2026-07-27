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
        BotCommand(command="about", description="About Nihao-chan ✨")
    ]
    
    commands_ru = [
        BotCommand(command="start", description="Запустить бота / Меню 🌸"),
        BotCommand(command="help", description="Показать справку ℹ️"),
        BotCommand(command="about", description="О Нихао-тян ✨")
    ]
    
    try:
        # Русский язык по умолчанию для всех остальных локалей
        await bot.set_my_commands(commands_ru)
        
        # Индивидуальные настройки меню для RU и EN локалей
        await bot.set_my_commands(commands_ru, language_code="ru")
        await bot.set_my_commands(commands_en, language_code="en")
        logger.info("Локализованные команды меню успешно зарегистрированы.")
    except Exception as e:
        logger.error(f"Ошибка при установке меню команд: {e}")


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

    # 2. Инициализация бота и диспетчера.
    # Настраиваем HTML разметку сообщений по умолчанию для красивого форматирования.
    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    from database.fsm_storage import SQLAlchemyStorage
    storage = SQLAlchemyStorage(AsyncSessionLocal)
    dp = Dispatcher(storage=storage)

    # 3. Регистрация Middleware (прослоек).
    # Порядок регистрации критически важен:
    # 1) Сессия БД — открывает транзакцию и передает ее в следующие слои.
    # 2) Баны — проверяет статус блокировки и регистрирует новых пользователей.
    # 3) Антифлуд (Троттлинг) — защищает бот от спам-сообщений.
    # 4) Логирование — записывает поступающие события в логи.
    dp.update.outer_middleware(DbSessionMiddleware(AsyncSessionLocal))
    dp.update.outer_middleware(BanMiddleware())
    i18n_middleware.setup(dp)
    dp.message.outer_middleware(ThrottlingMiddleware())
    dp.message.outer_middleware(LoggingMiddleware())
    dp.callback_query.outer_middleware(LoggingMiddleware())

    # 4. Подключение общего роутера хендлеров
    dp.include_router(get_main_router())

    # 5. Установка команд меню
    await set_bot_commands(bot)

    # 6. Пропуск накопившихся обновлений перед стартом (drop_pending_updates)
    await bot.delete_webhook(drop_pending_updates=True)

    # Запускаем фоновый планировщик перезапуска в полночь
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
