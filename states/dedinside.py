from aiogram.fsm.state import StatesGroup, State


class DedinsideStates(StatesGroup):
    """
    Состояния FSM для работы команды /dedinside.
    """
    selecting_count = State()      # Выбор количества сообщений (5 или 10)
    waiting_for_message = State()  # Ожидание текстового сообщения от пользователя
    sending_spam = State()         # Процесс отправки и удаления повторяющихся сообщений
