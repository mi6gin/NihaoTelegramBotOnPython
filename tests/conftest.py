import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.engine import Base
from database.models.user import User
from database.models.ticket import Ticket

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Фикстура для создания изолированной базы данных в оперативной памяти (in-memory SQLite)
    и предоставления асинхронной сессии для каждого теста.
    """
    # Создаем асинхронный движок для in-memory SQLite базы данных
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Автоматически создаем таблицы в изолированной тестовой БД
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Создаем фабрику сессий
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Возвращаем сессию в тест
    async with async_session() as session:
        yield session

    # Закрываем подключение к БД
    await engine.dispose()
