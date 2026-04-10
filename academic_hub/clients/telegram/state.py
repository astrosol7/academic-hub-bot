from aiogram.fsm.state import State, StatesGroup


class HubStates(StatesGroup):
    home = State()
    resources = State()
    quarter = State()
    course = State()
    more_files = State()
    week_list = State()
    week_category = State()

