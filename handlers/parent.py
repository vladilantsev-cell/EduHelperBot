from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from database import get_user, get_schedule, get_events, register_for_event
from database import get_debts, get_payments_history, get_grades
from keyboards import get_main_keyboard, get_back_keyboard, get_certificate_keyboard

router = Router()


class ParentState(StatesGroup):
    waiting_for_feedback = State()
    waiting_for_certificate = State()
    waiting_for_certificate_name = State()
    waiting_for_meeting_date = State()
    waiting_for_meeting_teacher = State()


@router.message(F.text.in_([
    "📚 Расписание", "💰 Финансы", "🎉 Мероприятия", "📊 Успеваемость",
    "📄 Справки", "📰 Новости", "👨‍🏫 Связаться с учителем",
    "📅 Запись на встречу", "❓ Помощь", "🚪 Выход", "🔙 Назад"
]))
async def parent_menu(message: types.Message, state: FSMContext):
    text = message.text

    if text == "📚 Расписание":
        await show_schedule(message)
    elif text == "💰 Финансы":
        await show_finance(message)
    elif text == "🎉 Мероприятия":
        await show_events(message)
    elif text == "📊 Успеваемость":
        await show_grades(message)
    elif text == "📄 Справки":
        await show_certificates(message, state)
    elif text == "📰 Новости":
        await show_news(message)
    elif text == "👨‍🏫 Связаться с учителем":
        await ask_feedback(message, state)
    elif text == "📅 Запись на встречу":
        await ask_meeting(message, state)
    elif text == "❓ Помощь":
        await show_help(message)
    elif text == "🚪 Выход":
        await logout(message, state)
    elif text == "🔙 Назад":
        await go_back(message, state)


async def show_schedule(message: types.Message):
    user = get_user(message.from_user.id)
    schedule = get_schedule(user.id)

    if not schedule:
        await message.answer("📅 На сегодня расписания нет", reply_markup=get_back_keyboard())
        return

    text = "📅 *Расписание:*\n\n"
    for lesson in schedule:
        text += f"📖 *{lesson.lesson_name}*\n🕐 {lesson.date_time.strftime('%H:%M')}\n📍 {lesson.location}\n👨‍🏫 {lesson.teacher}\n\n"

    await message.answer(text, parse_mode="Markdown", reply_markup=get_back_keyboard())


async def show_finance(message: types.Message):
    user = get_user(message.from_user.id)
    debts = get_debts(user.id)
    payments = get_payments_history(user.id)

    text = "💰 *Финансы*\n\n📌 *Задолженности:*\n"
    if debts:
        for debt in debts:
            text += f"• {debt.amount} руб.\n"
    else:
        text += "✅ Нет задолженностей\n"

    text += "\n📜 *История платежей:*\n"
    for p in payments[:5]:
        status = "✅" if p.status == "paid" else "⚠️"
        text += f"{status} {p.amount} руб.\n"

    await message.answer(text, parse_mode="Markdown", reply_markup=get_back_keyboard())


async def show_events(message: types.Message):
    events = get_events()
    if not events:
        await message.answer("🎉 Нет мероприятий", reply_markup=get_back_keyboard())
        return

    text = "🎉 *Мероприятия:*\n\n"
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])

    for event in events:
        text += f"📌 *{event.title}*\n📝 {event.description}\n📅 {event.date.strftime('%d.%m.%Y %H:%M')}\n\n"
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(text=f"✅ {event.title}", callback_data=f"reg_{event.id}")
        ])

    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)


async def show_grades(message: types.Message):
    user = get_user(message.from_user.id)
    grades = get_grades(user.id)

    if not grades:
        await message.answer("📊 Нет оценок", reply_markup=get_back_keyboard())
        return

    avg = sum(g.grade for g in grades) / len(grades)
    text = f"📊 *Успеваемость*\n\n📈 *Средний балл:* {avg:.1f}\n\n"

    for grade in grades:
        text += f"📖 *{grade.subject}*: {grade.grade}\n💬 {grade.teacher_feedback}\n📅 {grade.date.strftime('%d.%m.%Y')}\n\n"

    await message.answer(text, parse_mode="Markdown", reply_markup=get_back_keyboard())


async def show_certificates(message: types.Message, state: FSMContext):
    await message.answer("📄 Выберите справку:", reply_markup=get_certificate_keyboard())
    await state.set_state(ParentState.waiting_for_certificate)


async def show_news(message: types.Message):
    news = "🏆 Поздравляем победителей!\n\n📢 День открытых дверей 25 марта!\n\n🎨 Конкурс рисунков до 30 марта!"
    await message.answer(f"📰 *Новости*\n\n{news}", parse_mode="Markdown", reply_markup=get_back_keyboard())


async def ask_feedback(message: types.Message, state: FSMContext):
    await message.answer("✍️ Напишите предмет:", reply_markup=get_back_keyboard())
    await state.set_state(ParentState.waiting_for_feedback)


async def ask_meeting(message: types.Message, state: FSMContext):
    await message.answer("📅 Введите дату и время:", reply_markup=get_back_keyboard())
    await state.set_state(ParentState.waiting_for_meeting_date)


async def show_help(message: types.Message):
    help_text = "❓ *Помощь*\n\n📚 Расписание\n💰 Финансы\n🎉 Мероприятия\n📊 Успеваемость\n📄 Справки\n👨‍🏫 Связаться с учителем\n📅 Запись на встречу"
    await message.answer(help_text, parse_mode="Markdown", reply_markup=get_back_keyboard())


async def logout(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("👋 До свидания!", reply_markup=types.ReplyKeyboardRemove())


async def go_back(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id)
    await state.clear()
    await message.answer("Главное меню:", reply_markup=get_main_keyboard(user.role))


@router.message(ParentState.waiting_for_feedback)
async def process_feedback(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id)
    await message.bot.send_message(ADMIN_ID, f"📝 Запрос от {user.full_name}: {message.text}")
    await state.clear()
    await message.answer("✅ Отправлено!", reply_markup=get_main_keyboard(user.role))


@router.message(ParentState.waiting_for_certificate)
async def process_certificate(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await go_back(message, state)
        return
    await state.update_data(cert_type=message.text)
    await message.answer("📝 Введите ФИО ученика:")
    await state.set_state(ParentState.waiting_for_certificate_name)


@router.message(ParentState.waiting_for_certificate_name)
async def process_certificate_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user = get_user(message.from_user.id)
    await message.bot.send_message(ADMIN_ID,
                                   f"📄 Справка {data.get('cert_type')} для {message.text} от {user.full_name}")
    await state.clear()
    await message.answer("✅ Заказ отправлен!", reply_markup=get_main_keyboard(user.role))


@router.message(ParentState.waiting_for_meeting_date)
async def process_meeting_date(message: types.Message, state: FSMContext):
    await state.update_data(meeting_date=message.text)
    await message.answer("👨‍🏫 Введите ФИО преподавателя:")
    await state.set_state(ParentState.waiting_for_meeting_teacher)


@router.message(ParentState.waiting_for_meeting_teacher)
async def process_meeting_teacher(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user = get_user(message.from_user.id)
    await message.bot.send_message(ADMIN_ID,
                                   f"📅 Встреча {data.get('meeting_date')} с {message.text} от {user.full_name}")
    await state.clear()
    await message.answer("✅ Запрос отправлен!", reply_markup=get_main_keyboard(user.role))


@router.callback_query(lambda c: c.data.startswith("reg_"))
async def handle_registration(callback: types.CallbackQuery):
    event_id = int(callback.data.split("_")[1])
    success = register_for_event(callback.from_user.id, event_id)

    if success:
        await callback.answer("✅ Вы зарегистрированы!")
        await callback.bot.send_message(ADMIN_ID, f"🎉 Регистрация от {callback.from_user.id}")
    else:
        await callback.answer("❌ Уже зарегистрированы")

    await callback.message.delete()