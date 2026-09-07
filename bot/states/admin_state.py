from aiogram.fsm.state import State, StatesGroup


class AdminState(StatesGroup):
    waiting_add_admin_id = State()
    waiting_remove_admin_id = State()
    waiting_test_file = State()


class UserCodeEntryState(StatesGroup):
    waiting_test_code = State()
