"""Global Telegram error handlers."""

import html
import traceback
import time
from aiogram import Router, Bot
from aiogram.types import ErrorEvent
from config.settings import settings
from utils.logger import logger

router = Router(name="error_router")

# Временный кэш для предотвращения флуда ошибками
# { "hash_ошибки": timestamp_последней_отправки }
error_cache = {}
THROTTLING_INTERVAL = 300  # 5 минут


@router.errors()
async def global_error_handler(event: ErrorEvent, bot: Bot):
    """
    Глобальный обработчик ошибок. Логирует исключение и отправляет
    детализированный отчет администраторам с защитой от флуда.
    """
    exception = event.exception
    
    # 1. Логируем ошибку локально в файлы
    logger.error(f"Critical error occurred: {exception}", exc_info=exception)

    # 2. Генерируем хэш ошибки для защиты от флуда
    tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
    tb_text = "".join(tb_lines)
    
    # Ключ состоит из типа ошибки и последней строки трейсбека (где обычно указано место ошибки)
    error_key = f"{type(exception).__name__}:{tb_lines[-1] if tb_lines else ''}"
    
    current_time = time.time()
    if error_key in error_cache:
        if current_time - error_cache[error_key] < THROTTLING_INTERVAL:
            # Ошибка произошла недавно, пропускаем отправку админам
            return
            
    # Запоминаем время отправки
    error_cache[error_key] = current_time

    # 3. Собираем информацию о пользователе и событии
    user_info = "Неизвестный источник"
    action_info = "Неизвестное действие"
    update = event.update

    if update.message:
        user = update.message.from_user
        if user:
            user_info = f"Имя: {html.escape(user.first_name)} (ID: <code>{user.id}</code>, @{user.username or 'нет'})"
        action_info = f"Текст сообщения: <code>{html.escape(update.message.text or 'пусто')}</code>"
    elif update.callback_query:
        user = update.callback_query.from_user
        if user:
            user_info = f"Имя: {html.escape(user.first_name)} (ID: <code>{user.id}</code>, @{user.username or 'нет'})"
        action_info = f"Нажатие кнопки (callback_data): <code>{html.escape(update.callback_query.data or 'пусто')}</code>"

    # Экранируем трейсбек для безопасного вывода в HTML
    safe_tb = html.escape(tb_text)
    if len(safe_tb) > 3000:
        safe_tb = safe_tb[:3000] + "\n\n[...Трейсбек обрезан из-за ограничений Telegram...]"

    # Формируем красивое HTML сообщение
    alert_text = (
        f"⚠️ <b>Критическое исключение в боте!</b>\n\n"
        f"👤 <b>Пользователь:</b> {user_info}\n"
        f"🎬 <b>Действие:</b> {action_info}\n\n"
        f"❌ <b>Ошибка:</b> <code>{html.escape(str(exception))}</code>\n\n"
        f"📝 <b>Трейсбек:</b>\n<pre><code class='language-python'>{safe_tb}</code></pre>"
    )

    # 4. Рассылаем уведомление администраторам
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(chat_id=admin_id, text=alert_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Не удалось отправить алерт об ошибке админу {admin_id}: {e}")
