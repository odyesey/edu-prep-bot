from aiogram.fsm.state import State, StatesGroup

class Verify(StatesGroup):
    channel = State()

class HostTest(StatesGroup):
    rated = State()
    name = State()
    file = State()
    description = State()
    time = State()
    duration = State()
    answers = State()

class AddResource(StatesGroup):
    title = State()
    file = State()
    description = State()
    keywords = State()

class AddVocabulary(StatesGroup):
    title = State()
    words = State()
    keywords = State()
