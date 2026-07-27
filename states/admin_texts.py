from aiogram.fsm.state import StatesGroup, State


class AdminTextStates(StatesGroup):
    """
    Состояния FSM для редактирования динамических текстов бота администратором.
    """
    waiting_for_text_content = State()
