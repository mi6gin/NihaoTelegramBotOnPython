import os
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config.settings import settings
from utils.logger import logger

# Автоматически создаем директорию для базы данных, если используется SQLite
try:
    db_url_parsed = make_url(settings.db_url)
    if db_url_parsed.drivername.startswith("sqlite") and db_url_parsed.database:
        db_dir = os.path.dirname(db_url_parsed.database)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
except Exception as e:
    logger.error(f"Не удалось подготовить директорию для БД: {e}")

# Создаем асинхронный движок для подключения к БД
engine = create_async_engine(
    url=settings.db_url,
    echo=False,  # Можно включить True для отладки SQL-запросов
    future=True
)

from sqlalchemy import event

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
    except Exception:
        pass
    finally:
        cursor.close()

# Фабрика асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """
    Базовый декларативный класс для моделей SQLAlchemy.
    """
    pass


async def init_db():
    """
    Создает все таблицы базы данных, если они еще не существуют,
    а также автоматически добавляет новые колонки в существующие таблицы (автомиграция).
    """
    try:
        logger.info("Инициализация базы данных...")
        async with engine.begin() as conn:
            # Импортируем модели перед созданием таблиц, чтобы они зарегистрировались в Base.metadata
            from database.models.user import User
            from database.models.ticket import Ticket
            from database.models.fsm_state import FSMStateModel
            from database.models.bot_text import BotText
            from database.models.favorite_tiktok import FavoriteTikTok
            from sqlalchemy import inspect, text
            
            await conn.run_sync(Base.metadata.create_all)

            def _auto_migrate(connection):
                inspector = inspect(connection)
                tables = inspector.get_table_names()
                if "favorite_tiktoks" in tables:
                    columns = [col["name"] for col in inspector.get_columns("favorite_tiktoks")]
                    if "file_id" not in columns:
                        logger.info("Автомиграция: Добавление колонки file_id в таблицу favorite_tiktoks...")
                        connection.execute(text("ALTER TABLE favorite_tiktoks ADD COLUMN file_id VARCHAR(256)"))

            await conn.run_sync(_auto_migrate)

        logger.info("База данных успешно инициализирована.")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}", exc_info=True)
        raise e
