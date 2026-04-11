from aiogram.fsm.state import State, StatesGroup

class AuthState(StatesGroup):
    waiting_for_role = State()
    waiting_for_login = State()
    waiting_for_password = State()

class ParentState(StatesGroup):
    main_menu = State()
    waiting_for_feedback_request = State()
    waiting_for_certificate_type = State()
    waiting_for_certificate_name = State()
    waiting_for_meeting_teacher = State()
    waiting_for_meeting_datetime = State()

class StudentState(StatesGroup):
    main_menu = State()
    waiting_for_teacher_message = State()

class AdminState(StatesGroup):
    main_menu = State()
    waiting_event_title = State()
    waiting_event_description = State()
    waiting_event_date = State()
    waiting_news_text = State()
    waiting_boost_user_id = State()
    waiting_boost_amount = State()
    waiting_boost_reason = State()
    waiting_shop_name = State()
    waiting_shop_description = State()
    waiting_shop_price = State()
    waiting_schedule_student_id = State()
    waiting_schedule_lesson = State()
    waiting_schedule_datetime = State()
    waiting_schedule_location = State()
    waiting_schedule_teacher = State()
