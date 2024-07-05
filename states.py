from aiogram.dispatcher.filters.state import State, StatesGroup

class QuizStates(StatesGroup):
    CHOOSING_PART = State()
    CHOOSING_LEVEL = State()
    TAKING_QUIZ = State()

class ProfileStates(StatesGroup):
    SETTING_PROFILE = State()
    SETTING_NAME = State()
    SETTING_FACULTY = State()
    SETTING_YEAR = State()
    SETTING_QUIDDITCH_ROLE = State()
    CHOOSING_SUBJECT = State()
    SETTING_GRADE = State()
    EDITING_PROFILE = State()
    DELETING_PROFILE = State()
    EDIT_NAME = State()
    EDIT_FACULTY = State()
    EDIT_YEAR = State()
    EDIT_QUIDDITCH_ROLE = State()
