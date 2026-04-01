import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Состояния для FSM
class States:
    WAITING_FOR_LOGIN = "waiting_for_login"
    WAITING_FOR_PASSWORD = "waiting_for_password"
    WAITING_FOR_FEEDBACK = "waiting_for_feedback"
    WAITING_FOR_CERTIFICATE = "waiting_for_certificate"
    WAITING_FOR_MEETING_DATE = "waiting_for_meeting_date"
    WAITING_FOR_MEETING_TEACHER = "waiting_for_meeting_teacher"