from aiogram.fsm.state import State, StatesGroup


class HubStates(StatesGroup):
    home = State()
    resources = State()
    quarter = State()
    course = State()
    more_files = State()
    week_list = State()
    week_category = State()
    about = State()
    report = State()
    report_description = State()
    search = State()
    suggest = State()
    verify = State()
    ask_title = State()
    ask_body = State()
    answer_body = State()
