import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery
from aiogram_i18n import I18nContext
from presentation.telegram.admin.panel import get_logs_file


@pytest.mark.asyncio
async def test_get_logs_file_success():
    """
    Тестирует успешную отправку логов администратору.
    Проверяет вызовы answer(), инициализацию FSInputFile и отправку документа.
    """
    callback = AsyncMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.message = AsyncMock()
    callback.message.answer_document = AsyncMock()
    
    i18n = MagicMock(spec=I18nContext)
    i18n.get.return_value = "📄 Current bot log file"

    # Патчим проверку файла и FSInputFile, чтобы изолировать тест от файловой системы
    with patch("os.path.exists", return_value=True), \
         patch(
             "presentation.telegram.admin.panel.FSInputFile"
         ) as mock_fs_input_file:
         
        mock_fs_input_file.return_value = "mocked_document_file"
        
        await get_logs_file(callback, i18n)
        
        # 1. Должен быть вызван ответ на callback
        callback.answer.assert_called_once()
        
        # 2. Должен создаваться объект документа
        mock_fs_input_file.assert_called_once()
        
        # 3. Документ должен быть отправлен в чат
        callback.message.answer_document.assert_called_once_with(
            document="mocked_document_file",
            caption="📄 Current bot log file"
        )


@pytest.mark.asyncio
async def test_get_logs_file_not_found():
    """
    Тестирует случай, когда файл логов отсутствует на сервере.
    Проверяет отправку сообщения об ошибке.
    """
    callback = AsyncMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.message = AsyncMock()
    callback.message.answer = AsyncMock()
    
    i18n = MagicMock(spec=I18nContext)
    i18n.get.return_value = "❌ Log file not found on the server."

    with patch("os.path.exists", return_value=False):
        await get_logs_file(callback, i18n)
        
        # 1. Должен быть вызван ответ на callback
        callback.answer.assert_called_once()
        
        # 2. Должно быть отправлено сообщение об ошибке
        callback.message.answer.assert_called_once_with("❌ Log file not found on the server.")
