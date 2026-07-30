import asyncio

from aiogram import Bot
from aiogram.types import BotCommand

from utils.logger import logger

COMMAND_REGISTRATION_ATTEMPTS = 3
COMMAND_REGISTRATION_RETRY_DELAY = 3


def _commands(*descriptions: tuple[str, str]) -> list[BotCommand]:
    return [
        BotCommand(command=command, description=description)
        for command, description in descriptions
    ]


COMMANDS_BY_LOCALE = {
    "ru": _commands(
        ("start", "Запустить бота / Меню 🌸"),
        ("help", "Показать справку ℹ️"),
        ("about", "О Нихао-тян ✨"),
        ("dedinside", "Особый режим dedinside 🖤"),
        ("mtiktok", "Скачать аудио из TikTok 🎵"),
        ("ptiktok", "Скачать слайдшоу из TikTok 🖼️"),
    ),
    "en": _commands(
        ("start", "Launch the bot / Menu 🌸"),
        ("help", "Show help info ℹ️"),
        ("about", "About Nihao-chan ✨"),
        ("dedinside", "Special dedinside mode 🖤"),
        ("mtiktok", "Download TikTok audio MP3 🎵"),
        ("ptiktok", "Download TikTok slideshow 🖼️"),
    ),
}


async def set_bot_commands(bot: Bot) -> None:
    """Register the default and localized Telegram command menus."""
    for attempt in range(1, COMMAND_REGISTRATION_ATTEMPTS + 1):
        try:
            await bot.set_my_commands(
                COMMANDS_BY_LOCALE["ru"],
                request_timeout=30,
            )
            try:
                for locale, commands in COMMANDS_BY_LOCALE.items():
                    await bot.set_my_commands(
                        commands,
                        language_code=locale,
                        request_timeout=30,
                    )
            except Exception as error:
                logger.debug("Локализованные меню пропущены: %s", error)

            logger.info("Команды меню бота успешно зарегистрированы.")
            return
        except Exception as error:
            if attempt == COMMAND_REGISTRATION_ATTEMPTS:
                logger.warning(
                    "Не удалось установить меню команд "
                    "(проблемы сети Telegram API): %s",
                    error,
                )
            else:
                await asyncio.sleep(COMMAND_REGISTRATION_RETRY_DELAY)
