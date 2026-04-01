from aiogram.dispatcher.filters.state import State, StatesGroup

class AuthState(StatesGroup):
    waiting_for_role = State()
    waiting_for_login = State()
    waiting_for_password = State()

class ParentState(StatesGroup):
    main_menu = State()
    waiting_for_feedback = State()
    waiting_for_certificate = State()
    waiting_for_certificate_name = State()
    waiting_for_meeting_date = State()
    waiting_for_meeting_teacher = State()

class StudentState(StatesGroup):
    main_menu = State()
    waiting_for_message = State()