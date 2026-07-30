import asyncio
import sys

from application.bootstrap import run_bot
from application.bot_commands import set_bot_commands
from application.lifecycle import schedule_midnight_restart
from utils.logger import logger


async def main() -> None:
    """Run the application."""
    await run_bot()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот Нихао-тян остановлен пользователем.")
    except Exception:
        logger.critical(
            "Критическая ошибка при работе бота",
            exc_info=True,
        )
        sys.exit(1)
