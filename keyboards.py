from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard(role):
    if role == "parent":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📚 Расписание"), KeyboardButton(text="💰 Финансы")],
                [KeyboardButton(text="🎉 Мероприятия"), KeyboardButton(text="📊 Успеваемость")],
                [KeyboardButton(text="📄 Справки"), KeyboardButton(text="📰 Новости")],
                [KeyboardButton(text="👨‍🏫 Связаться с учителем"), KeyboardButton(text="📅 Запись на встречу")],
                [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="🚪 Выход")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⭐ Мои бусты"), KeyboardButton(text="🎉 Мероприятия")],
                [KeyboardButton(text="📚 Расписание"), KeyboardButton(text="📖 Материалы")],
                [KeyboardButton(text="👨‍🏫 Написать учителю"), KeyboardButton(text="❓ Помощь")],
                [KeyboardButton(text="🚪 Выход")]
            ],
            resize_keyboard=True
        )

def get_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True
    )

def get_certificate_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Справка об обучении")],
            [KeyboardButton(text="Справка для налогового вычета")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )