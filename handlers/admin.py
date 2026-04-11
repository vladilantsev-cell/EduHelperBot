#   Панель администратора Movavik.

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from states import AdminState, AuthState
from keyboards import admin_main_keyboard, back_keyboard
from database import (
    get_user, get_all_users, logout_user,
    add_event, add_boost, add_shop_item, add_schedule,
    add_news, get_user_by_credentials,
)
from config import ADMIN_ID

router = Router()

# Защита: только авторизованные админы

def _is_admin(telegram_id: int) -> bool:
    user = get_user(telegram_id)
    return (user and user.role == "admin") or telegram_id == ADMIN_ID

# Выход

@router.message(AdminState.main_menu, F.text == "🚪 Выйти из админки")
async def admin_logout(message: Message, state: FSMContext):
    logout_user(message.from_user.id)
    await state.clear()
    await state.set_state(AuthState.waiting_for_role)
    from keyboards import role_keyboard
    await message.answer("👋 Вы вышли из панели администратора.", reply_markup=role_keyboard())

# Список пользователей

@router.message(AdminState.main_menu, F.text == "📋 Все пользователи")
async def admin_users(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return

    users = get_all_users()
    if not users:
        await message.answer("Пользователей пока нет.", reply_markup=admin_main_keyboard())
        return

    text = f"👥 <b>Пользователи бота ({len(users)}):</b>\n\n"
    role_icon = {"student": "🎓", "parent": "👨‍👩‍👧", "admin": "🔑"}
    for u in users:
        icon = role_icon.get(u.role, "❓")
        text += f"{icon} <b>{u.full_name}</b> (@{u.username or '—'}) — ID: {u.telegram_id}\n"

    await message.answer(text, reply_markup=admin_main_keyboard(), parse_mode="HTML")

# Рассылка новостей

@router.message(AdminState.main_menu, F.text == "📢 Рассылка новостей")
async def admin_news_start(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.set_state(AdminState.waiting_news_text)
    await message.answer(
        "📢 Напишите текст новости.\nОна будет отправлена всем пользователям бота:",
        reply_markup=back_keyboard(),
    )

@router.message(AdminState.waiting_news_text, F.text == "🔙 Назад")
async def admin_news_back(message: Message, state: FSMContext):
    await state.set_state(AdminState.main_menu)
    await message.answer("Панель администратора:", reply_markup=admin_main_keyboard())

@router.message(AdminState.waiting_news_text)
async def admin_news_send(message: Message, state: FSMContext):
    news_text = message.text.strip()
    add_news(news_text)

    users = get_all_users()
    sent, failed = 0, 0
    for u in users:
        if u.telegram_id:
            try:
                await message.bot.send_message(
                    u.telegram_id,
                    f"📰 <b>Новости школы Movavi</b>\n\n{news_text}",
                    parse_mode="HTML",
                )
                sent += 1
            except Exception:
                failed += 1

    await state.set_state(AdminState.main_menu)
    await message.answer(
        f"✅ Рассылка завершена!\n"
        f"📨 Отправлено: {sent}\n❌ Ошибок: {failed}",
        reply_markup=admin_main_keyboard(),
    )

# Добавление мероприятия

@router.message(AdminState.main_menu, F.text == "🗓 Добавить мероприятие")
async def admin_event_start(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.set_state(AdminState.waiting_event_title)
    await message.answer("Введите <b>название</b> мероприятия:", reply_markup=back_keyboard(),
                         parse_mode="HTML")

@router.message(AdminState.waiting_event_title, F.text == "🔙 Назад")
async def admin_event_back(message: Message, state: FSMContext):
    await state.set_state(AdminState.main_menu)
    await message.answer("Панель администратора:", reply_markup=admin_main_keyboard())

@router.message(AdminState.waiting_event_title)
async def admin_event_title(message: Message, state: FSMContext):
    await state.update_data(event_title=message.text.strip())
    await state.set_state(AdminState.waiting_event_description)
    await message.answer("Введите <b>описание</b> мероприятия:", parse_mode="HTML")

@router.message(AdminState.waiting_event_description)
async def admin_event_description(message: Message, state: FSMContext):
    await state.update_data(event_description=message.text.strip())
    await state.set_state(AdminState.waiting_event_date)
    await message.answer(
        "Введите <b>дату и время</b> (например: 25.05.2026 15:00):",
        parse_mode="HTML",
    )

@router.message(AdminState.waiting_event_date)
async def admin_event_date(message: Message, state: FSMContext):
    from datetime import datetime
    try:
        dt = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer("❌ Неверный формат. Введите дату в виде: 25.05.2026 15:00")
        return

    data = await state.get_data()
    add_event(data["event_title"], data["event_description"], dt)
    await state.set_state(AdminState.main_menu)
    await message.answer(
        f"✅ Мероприятие <b>{data['event_title']}</b> добавлено!",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML",
    )

# Начисление бустов

@router.message(AdminState.main_menu, F.text == "⭐ Начислить бусты")
async def admin_boost_start(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return

    users = get_all_users()
    students = [u for u in users if u.role == "student"]
    if not students:
        await message.answer("Нет зарегистрированных учеников.", reply_markup=admin_main_keyboard())
        return

    text = "🎓 <b>Ученики:</b>\n\n"
    for u in students:
        text += f"  ID: <code>{u.id}</code> — {u.full_name}\n"
    text += "\nВведите <b>ID ученика</b> из списка выше:"

    await state.set_state(AdminState.waiting_boost_user_id)
    await message.answer(text, reply_markup=back_keyboard(), parse_mode="HTML")

@router.message(AdminState.waiting_boost_user_id, F.text == "🔙 Назад")
async def admin_boost_back(message: Message, state: FSMContext):
    await state.set_state(AdminState.main_menu)
    await message.answer("Панель администратора:", reply_markup=admin_main_keyboard())

@router.message(AdminState.waiting_boost_user_id)
async def admin_boost_user(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите числовой ID.")
        return
    await state.update_data(boost_user_id=uid)
    await state.set_state(AdminState.waiting_boost_amount)
    await message.answer("Введите <b>количество бустов</b> для начисления:", parse_mode="HTML")

@router.message(AdminState.waiting_boost_amount)
async def admin_boost_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите положительное число.")
        return
    await state.update_data(boost_amount=amount)
    await state.set_state(AdminState.waiting_boost_reason)
    await message.answer("Введите <b>причину</b> начисления (например: За победу на олимпиаде):",
                         parse_mode="HTML")

@router.message(AdminState.waiting_boost_reason)
async def admin_boost_reason(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data["boost_user_id"]
    amount = data["boost_amount"]
    reason = message.text.strip()

    add_boost(user_id, amount, reason)

    # Уведомляем ученика
    from database import Session, User
    s = Session()
    student = s.query(User).get(user_id)
    s.close()
    if student and student.telegram_id:
        try:
            await message.bot.send_message(
                student.telegram_id,
                f"⭐ Вам начислено <b>{amount} Movavi Boost</b>!\n\nПричина: {reason}",
                parse_mode="HTML",
            )
        except Exception:
            pass

    await state.set_state(AdminState.main_menu)
    await message.answer(
        f"✅ Начислено {amount} 🪙 пользователю (ID: {user_id})\nПричина: {reason}",
        reply_markup=admin_main_keyboard(),
    )

# Добавлние товара в магазин

@router.message(AdminState.main_menu, F.text == "🛒 Добавить товар")
async def admin_shop_start(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.set_state(AdminState.waiting_shop_name)
    await message.answer("Введите <b>название товара</b>:", reply_markup=back_keyboard(),
                         parse_mode="HTML")

@router.message(AdminState.waiting_shop_name, F.text == "🔙 Назад")
async def admin_shop_back(message: Message, state: FSMContext):
    await state.set_state(AdminState.main_menu)
    await message.answer("Панель администратора:", reply_markup=admin_main_keyboard())

@router.message(AdminState.waiting_shop_name)
async def admin_shop_name(message: Message, state: FSMContext):
    await state.update_data(shop_name=message.text.strip())
    await state.set_state(AdminState.waiting_shop_description)
    await message.answer("Введите <b>описание товара</b>:", parse_mode="HTML")

@router.message(AdminState.waiting_shop_description)
async def admin_shop_description(message: Message, state: FSMContext):
    await state.update_data(shop_description=message.text.strip())
    await state.set_state(AdminState.waiting_shop_price)
    await message.answer("Введите <b>цену в бустах</b>:", parse_mode="HTML")

@router.message(AdminState.waiting_shop_price)
async def admin_shop_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите положительное число.")
        return

    data = await state.get_data()
    add_shop_item(data["shop_name"], data["shop_description"], price)
    await state.set_state(AdminState.main_menu)
    await message.answer(
        f"✅ Товар <b>{data['shop_name']}</b> ({price} 🪙) добавлен в магазин!",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML",
    )

# Добавление занятия в расписание

@router.message(AdminState.main_menu, F.text == "📝 Добавить занятие")
async def admin_schedule_start(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return

    from database import Session, User
    s = Session()
    students = s.query(User).filter_by(role="student").all()
    s.close()

    if not students:
        await message.answer("Нет зарегистрированных учеников.", reply_markup=admin_main_keyboard())
        return

    text = "🎓 <b>Ученики:</b>\n\n"
    for u in students:
        text += f"  ID: <code>{u.id}</code> — {u.full_name}\n"
    text += "\nВведите <b>ID ученика</b>:"

    await state.set_state(AdminState.waiting_schedule_student_id)
    await message.answer(text, reply_markup=back_keyboard(), parse_mode="HTML")

@router.message(AdminState.waiting_schedule_student_id, F.text == "🔙 Назад")
async def admin_sched_back(message: Message, state: FSMContext):
    await state.set_state(AdminState.main_menu)
    await message.answer("Панель администратора:", reply_markup=admin_main_keyboard())

@router.message(AdminState.waiting_schedule_student_id)
async def admin_sched_student(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите числовой ID.")
        return
    await state.update_data(sched_student_id=uid)
    await state.set_state(AdminState.waiting_schedule_lesson)
    await message.answer("Введите <b>название урока</b>:", parse_mode="HTML")

@router.message(AdminState.waiting_schedule_lesson)
async def admin_sched_lesson(message: Message, state: FSMContext):
    await state.update_data(sched_lesson=message.text.strip())
    await state.set_state(AdminState.waiting_schedule_datetime)
    await message.answer("Введите <b>дату и время урока</b> (например: 25.05.2026 09:00):",
                         parse_mode="HTML")

@router.message(AdminState.waiting_schedule_datetime)
async def admin_sched_datetime(message: Message, state: FSMContext):
    from datetime import datetime
    try:
        dt = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer("❌ Неверный формат. Введите: 25.05.2026 09:00")
        return
    await state.update_data(sched_dt=dt)
    await state.set_state(AdminState.waiting_schedule_location)
    await message.answer("Введите <b>место проведения</b> (например: Каб. 101):", parse_mode="HTML")

@router.message(AdminState.waiting_schedule_location)
async def admin_sched_location(message: Message, state: FSMContext):
    await state.update_data(sched_location=message.text.strip())
    await state.set_state(AdminState.waiting_schedule_teacher)
    await message.answer("Введите <b>ФИО преподавателя</b>:", parse_mode="HTML")

@router.message(AdminState.waiting_schedule_teacher)
async def admin_sched_teacher(message: Message, state: FSMContext):
    data = await state.get_data()
    add_schedule(
        lesson_name=data["sched_lesson"],
        date_time=data["sched_dt"],
        location=data["sched_location"],
        teacher=message.text.strip(),
        student_id=data["sched_student_id"],
    )
    await state.set_state(AdminState.main_menu)
    await message.answer(
        f"✅ Занятие <b>{data['sched_lesson']}</b> добавлено в расписание!",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML",
    )
