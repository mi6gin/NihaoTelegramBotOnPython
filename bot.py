import asyncio
import os
import sys

# Автоматически перезапускаем процесс через .venv/bin/python, если запуск выполнен не из виртуального окружения
_venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), ".venv", "bin", "python"))
if os.path.exists(_venv_python) and sys.executable != _venv_python:
    os.execv(_venv_python, [_venv_python] + sys.argv)

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
