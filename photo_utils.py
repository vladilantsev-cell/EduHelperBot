import os
from aiogram.types import FSInputFile

IMAGES_DIR = "images"


# Аватарка бота
def get_bot_avatar():
    return FSInputFile(os.path.join(IMAGES_DIR, "avatar.jpg"))


# Фото для разных разделов
def get_photo(menu_name: str):
    """Возвращает фото для указанного раздела меню"""
    photo_map = {
        # Главные меню (welcome)
        "welcome_parent": "welcome_parent.jpg",
        "welcome_student": "welcome_student.jpg",
        "welcome_admin": "welcome_admin.jpg",

        # Разделы для родителей и учеников
        "news": "menu_news.jpg",
        "schedule": "menu_schedule.jpg",
        "events": "menu_events.jpg",
        "materials": "menu_materials.jpg",
        "meeting": "menu_meeting.jpg",
        "help": "menu_help.jpg",
        "boosts": "menu_boosts.jpg",
        "message": "menu_message.jpg",
        "teacher": "menu_teacher.jpg",  # фото для раздела "Учитель"
        "finance": "menu_finance.jpg",
        "certificates": "menu_certificates.jpg",
        "grades": "menu_grades.jpg",
    }
    filename = photo_map.get(menu_name)
    if filename and os.path.exists(os.path.join(IMAGES_DIR, filename)):
        return FSInputFile(os.path.join(IMAGES_DIR, filename))
    return None


# Для инлайн-кнопок (мероприятия, магазин)
def get_photo_by_url(url: str):
    from aiogram.types import URLInputFile
    if url:
        return URLInputFile(url)
    return None