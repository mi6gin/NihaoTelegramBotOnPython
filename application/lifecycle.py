import asyncio
import datetime
import sys

from utils.logger import logger


def seconds_until_next_midnight(
    now: datetime.datetime | None = None,
) -> float:
    """Return the number of seconds until the next local midnight."""
    current_time = now or datetime.datetime.now()
    tomorrow = current_time.date() + datetime.timedelta(days=1)
    midnight = datetime.datetime.combine(
        tomorrow,
        datetime.time.min,
        tzinfo=current_time.tzinfo,
    )
    if current_time.tzinfo is not None:
        current_time = current_time.astimezone(datetime.timezone.utc)
        midnight = midnight.astimezone(datetime.timezone.utc)
    return (midnight - current_time).total_seconds()


async def schedule_midnight_restart() -> None:
    """Exit at the next local midnight so the process manager can restart."""
    seconds_to_wait = seconds_until_next_midnight()
    logger.info(
        "Запланирован автоперезапуск бота в 00:00. "
        "До перезапуска осталось %.1f сек.",
        seconds_to_wait,
    )

    await asyncio.sleep(seconds_to_wait)
    logger.info("Время 00:00. Инициируем мягкий перезапуск бота...")
    await asyncio.sleep(1)
    sys.exit(0)
