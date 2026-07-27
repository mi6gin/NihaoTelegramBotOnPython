import pytest
from unittest.mock import patch, AsyncMock
import datetime
from bot import schedule_midnight_restart


@pytest.mark.asyncio
async def test_schedule_midnight_restart():
    """Тест вычисления времени до перезапуска и корректного завершения процесса."""
    # Установим фиксированное текущее время: 2026-07-27 в 23:59:50
    fixed_now = datetime.datetime(2026, 7, 27, 23, 59, 50)
    
    # Мокаем класс datetime.datetime для возврата контролируемого текущего времени
    class MockDatetime(datetime.datetime):
        @classmethod
        def now(cls):
            return fixed_now

    # Мокаем asyncio.sleep и sys.exit, чтобы предотвратить реальное засыпание и выход
    with patch("datetime.datetime", MockDatetime), \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep, \
         patch("sys.exit") as mock_exit:
         
        await schedule_midnight_restart()
        
        # 1. Проверяем расчет времени ожидания.
        # От 2026-07-27 23:59:50 до полуночи 2026-07-28 00:00:00 ровно 10.0 секунд.
        mock_sleep.assert_any_call(10.0)
        # 2. Проверяем финальную паузу в 1.0 сек перед выходом.
        mock_sleep.assert_any_call(1.0)
        
        # 3. Проверяем вызов завершения процесса
        mock_exit.assert_called_once_with(0)
