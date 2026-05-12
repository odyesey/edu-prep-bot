from aiogram.fsm.state import State, StatesGroup

class HostTest(StatesGroup):
    name = State()
    file = State()
    description = State()
    time = State()
    duration = State()
    answers = State()

class Verify(StatesGroup):
    channel = State()
