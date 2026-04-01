from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from database import (
    get_user, get_schedule, get_events, register_for_event,
    get_boost, get_transactions, get_shop_items
)
from keyboards import get_main_keyboard, get_back_keyboard

router = Router()


class StudentState(StatesGroup):
    waiting_for_message = State()


@router.message(F.text.in_([
    "⭐ Мои бусты", "🎉 Мероприятия", "📚 Расписание",
    "📖 Материалы", "👨‍🏫 Написать учителю", "❓ Помощь", "🚪 Выход", "🔙 Назад"
]))
async def student_menu(message: types.Message, state: FSMContext):
    text = message.text

    if text == "⭐ Мои бусты":
        await show_boost(message)
    elif text == "🎉 Мероприятия":
        await show_events(message)
    elif text == "📚 Расписание":
        await show_schedule(message)
    elif text == "📖 Материалы":
        await show_materials(message)
    elif text == "👨‍🏫 Написать учителю":
        await ask_message(message, state)
    elif text == "❓ Помощь":
        await show_help(message)
    elif text == "🚪 Выход":
        await logout(message, state)
    elif text == "🔙 Назад":
        await go_back(message, state)


async def show_boost(message: types.Message):
    """Показать систему мотивации"""
    user = get_user(message.from_user.id)

    boosts = get_boost(user.id)
    transactions = get_transactions(user.id)
    shop_items = get_shop_items()

    text = "⭐ *Мои бусты*\n\n"
    text += f"💰 *Количество:* {boosts}\n\n"

    text += "📜 *История начислений:*\n"
    if transactions:
        for t in transactions[:5]:
            text += f"• {t.reason}: +{t.amount}⭐\n"
    else:
        text += "Пока нет операций\n"

    text += "\n🛒 *Магазин:*\n"
    for item in shop_items:
        text += f"• *{item.name}* - {item.price}⭐\n"
        text += f"  {item.description}\n"

    # Добавляем инлайн кнопки для магазина
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
    for item in shop_items:
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(
                text=f"🛍 Купить {item.name} за {item.price}⭐",
                callback_data=f"buy_{item.id}"
            )
        ])

    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)


async def show_events(message: types.Message):
    """Показать мероприятия"""
    user = get_user(message.from_user.id)
    events = get_events()

    if not events:
        await message.answer("🎉 Пока нет мероприятий", reply_markup=get_back_keyboard())
        return

    text = "🎉 *Мероприятия:*\n\n"
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])

    for event in events:
        registered = event.registered_users.split(",") if event.registered_users else []
        status = "✅ Зарегистрирован" if str(user.telegram_id) in registered else "❌ Не зарегистрирован"

        text += f"📌 *{event.title}*\n"
        text += f"📝 {event.description}\n"
        text += f"📅 {event.date.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"{status}\n\n"

        if str(user.telegram_id) not in registered:
            keyboard.inline_keyboard.append([
                types.InlineKeyboardButton(
                    text=f"✅ Записаться на {event.title}",
                    callback_data=f"student_reg_{event.id}"
                )
            ])

    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)


async def show_schedule(message: types.Message):
    """Показать расписание"""
    user = get_user(message.from_user.id)
    schedule = get_schedule(user.id)

    if not schedule:
        await message.answer("📅 На сегодня расписания нет", reply_markup=get_back_keyboard())
        return

    text = "📅 *Твое расписание:*\n\n"
    for lesson in schedule:
        text += f"📖 *{lesson.lesson_name}*\n"
        text += f"🕐 {lesson.date_time.strftime('%H:%M')}\n"
        text += f"📍 {lesson.location}\n"
        text += f"👨‍🏫 {lesson.teacher}\n\n"

    await message.answer(text, parse_mode="Markdown", reply_markup=get_back_keyboard())


async def show_materials(message: types.Message):
    """Показать учебные материалы"""
    materials = {
        "Математика": "https://example.com/math",
        "Русский язык": "https://example.com/russian",
        "Программирование": "https://example.com/programming",
        "Физика": "https://example.com/physics",
        "Английский": "https://example.com/english"
    }

    text = "📖 *Полезные материалы:*\n\n"
    for subject, link in materials.items():
        text += f"• *{subject}*: {link}\n"

    await message.answer(text, parse_mode="Markdown", reply_markup=get_back_keyboard())


async def ask_message(message: types.Message, state: FSMContext):
    """Написать сообщение учителю"""
    await message.answer(
        "✍️ Напиши сообщение для учителя:\n\n"
        "Например: У меня вопрос по домашнему заданию",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(StudentState.waiting_for_message)


async def show_help(message: types.Message):
    """Показать помощь"""
    help_text = (
        "❓ *Помощь по боту EduHelper*\n\n"
        "⭐ *Мои бусты* - твои баллы и магазин\n"
        "🎉 *Мероприятия* - анонсы и регистрация\n"
        "📚 *Расписание* - расписание уроков\n"
        "📖 *Материалы* - ссылки на учебники\n"
        "👨‍🏫 *Написать учителю* - отправить сообщение\n\n"
        "По всем вопросам пиши администратору."
    )

    await message.answer(help_text, parse_mode="Markdown", reply_markup=get_back_keyboard())


async def logout(message: types.Message, state: FSMContext):
    """Выход из аккаунта"""
    await state.clear()
    await message.answer(
        "👋 Ты вышел из аккаунта.\n\n"
        "Для входа используй /start",
        reply_markup=types.ReplyKeyboardRemove()
    )


async def go_back(message: types.Message, state: FSMContext):
    """Возврат в главное меню"""
    user = get_user(message.from_user.id)
    await state.clear()
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard(user.role)
    )


@router.message(StudentState.waiting_for_message)
async def process_message_to_teacher(message: types.Message, state: FSMContext):
    """Обработка сообщения учителю"""
    user = get_user(message.from_user.id)

    # Отправляем сообщение админу
    await message.bot.send_message(
        ADMIN_ID,
        f"💬 *СООБЩЕНИЕ УЧИТЕЛЮ*\n\n"
        f"👤 От: {user.full_name}\n"
        f"📱 ID: {message.from_user.id}\n"
        f"📝 Сообщение: {message.text}\n"
        f"🔗 Ссылка: tg://user?id={message.from_user.id}",
        parse_mode="Markdown"
    )

    await state.clear()
    await message.answer(
        "✅ Сообщение отправлено! Учитель ответит в ближайшее время.",
        reply_markup=get_main_keyboard(user.role)
    )


@router.callback_query(lambda c: c.data.startswith("student_reg_"))
async def handle_student_registration(callback: types.CallbackQuery):
    """Обработка регистрации на мероприятие для ученика"""
    event_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    success = register_for_event(user_id, event_id)

    if success:
        await callback.answer("✅ Ты зарегистрирован на мероприятие!")

        # Уведомляем админа
        await callback.bot.send_message(
            ADMIN_ID,
            f"🎉 *НОВАЯ РЕГИСТРАЦИЯ!*\n\n"
            f"👤 Ученик: {callback.from_user.id}\n"
            f"📱 Ссылка: tg://user?id={callback.from_user.id}",
            parse_mode="Markdown"
        )
    else:
        await callback.answer("❌ Ты уже зарегистрирован на это мероприятие")

    # Обновляем сообщение
    await callback.message.delete()
    await show_events(callback.message)


@router.callback_query(lambda c: c.data.startswith("buy_"))
async def handle_buy_item(callback: types.CallbackQuery):
    """Обработка покупки в магазине"""
    from database import get_shop_item, spend_boost, get_user

    item_id = int(callback.data.split("_")[1])
    item = get_shop_item(item_id)
    user = get_user(callback.from_user.id)

    if not item:
        await callback.answer("❌ Товар не найден")
        return

    success = spend_boost(user.id, item.price)

    if success:
        await callback.answer(f"✅ Ты купил {item.name}!")
        await callback.bot.send_message(
            ADMIN_ID,
            f"🛍 *ПОКУПКА В МАГАЗИНЕ*\n\n"
            f"👤 Ученик: {user.full_name}\n"
            f"🛒 Товар: {item.name}\n"
            f"💰 Цена: {item.price}⭐",
            parse_mode="Markdown"
        )

        # Обновляем сообщение
        await callback.message.delete()
        await show_boost(callback.message)
    else:
        await callback.answer(f"❌ Не хватает бустов! Нужно {item.price}⭐")