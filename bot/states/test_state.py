from aiogram.fsm.state import State, StatesGroup


class TestSessionState(StatesGroup):
    testing = State()               # Test jarayoni (savollar ko'rilmoqda)
    waiting_open_answer = State()   # Ochiq savol (36-45) uchun matn/son kiritilishi kutilmoqda
