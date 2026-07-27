from aiogram.fsm.state import StatesGroup, State


class TikTokStates(StatesGroup):
    """
    Состояния FSM для всех функций модуля TikTok.
    """
    waiting_for_username = State()     # Ввод юзернейма TikTok для привязки
    waiting_for_audio_link = State()   # Ввод ссылки для команды /Mtiktok (только звук)
    waiting_for_photo_link = State()   # Ввод ссылки для команды /Ptiktok (только слайдшоу)
    selecting_slides = State()         # Интерактивная сетка выбора конкретных слайдов
