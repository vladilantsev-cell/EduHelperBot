from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

def role_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="👨‍👩‍👧 Родитель"), KeyboardButton(text="🎓 Ученик")]],
        resize_keyboard=True,
    )

def parent_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Расписание"), KeyboardButton(text="💰 Финансы")],
            [KeyboardButton(text="🎉 Мероприятия"), KeyboardButton(text="📊 Успеваемость")],
            [KeyboardButton(text="📄 Справки"), KeyboardButton(text="📰 Новости")],
            [KeyboardButton(text="👨‍🏫 Учитель"), KeyboardButton(text="📅 Встреча")],
            [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="🚪 Выйти")],
        ],
        resize_keyboard=True,
    )

def student_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐ Мои бусты"), KeyboardButton(text="🎉 Мероприятия")],
            [KeyboardButton(text="📚 Расписание"), KeyboardButton(text="📖 Материалы")],
            [KeyboardButton(text="👨‍🏫 Написать учителю"), KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="🚪 Выйти")],
        ],
        resize_keyboard=True,
    )

def admin_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Все пользователи"), KeyboardButton(text="📢 Рассылка новостей")],
            [KeyboardButton(text="🗓 Добавить мероприятие"), KeyboardButton(text="⭐ Начислить бусты")],
            [KeyboardButton(text="🛒 Добавить товар"), KeyboardButton(text="📝 Добавить занятие")],
            [KeyboardButton(text="🚪 Выйти из админки")],
        ],
        resize_keyboard=True,
    )

def back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True,
    )

def certificate_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Справка об обучении")],
            [KeyboardButton(text="💼 Справка для налогового вычета")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
    )

def schedule_period_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 На сегодня"), KeyboardButton(text="📅 На неделю")],
            [KeyboardButton(text="📅 На месяц"), KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
    )

# мероприятия
def events_inline_keyboard(events, user_id):
    from database import is_registered_for_event
    buttons = []
    for e in events:
        already = is_registered_for_event(user_id, e.id)
        label = f"✅ {e.title}" if already else f"📌 {e.title}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"event_{e.id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def event_register_keyboard(event_id, already_registered: bool):
    if already_registered:
        btn = InlineKeyboardButton(text="✅ Вы записаны", callback_data="already_registered")
    else:
        btn = InlineKeyboardButton(text="📌 Записаться", callback_data=f"reg_{event_id}")
    return InlineKeyboardMarkup(inline_keyboard=[[btn],
        [InlineKeyboardButton(text="🔙 К списку", callback_data="events_list")]])

# магазин
def shop_inline_keyboard(items):
    buttons = [[InlineKeyboardButton(text=f"🛍 {i.name} — {i.price} 🪙", callback_data=f"shop_{i.id}")]
               for i in items]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def buy_inline_keyboard(item_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Купить", callback_data=f"buy_{item_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="shop_list")],
    ])