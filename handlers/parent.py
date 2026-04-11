from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import ParentState, AuthState
from keyboards import (
    parent_main_keyboard, back_keyboard,
    certificate_keyboard, schedule_period_keyboard,
    events_inline_keyboard, event_register_keyboard,
)
from database import (
    get_user, logout_user,
    get_schedule, get_full_schedule,
    get_events, get_event, register_for_event, is_registered_for_event,
    get_debts, get_payments_history,
    get_grades, calculate_average_grade,
    get_recent_news,
)
from config import ADMIN_ID
from photo_utils import get_photo

router = Router()


def _require_parent(state_filter=ParentState.main_menu):
    return state_filter


# ========== Выход ==========

@router.message(ParentState.main_menu, F.text == "🚪 Выйти")
async def parent_logout(message: Message, state: FSMContext):
    logout_user(message.from_user.id)
    await state.clear()
    await state.set_state(AuthState.waiting_for_role)
    from keyboards import role_keyboard
    await message.answer("👋 Вы вышли из системы. Используйте /start для входа.",
                         reply_markup=role_keyboard())


# ========== Расписание ==========

@router.message(ParentState.main_menu, F.text == "📚 Расписание")
async def parent_schedule(message: Message, state: FSMContext):
    photo = get_photo("schedule")
    if photo:
        await message.answer_photo(
            photo=photo,
            caption="📅 Выберите период расписания:",
            reply_markup=schedule_period_keyboard()
        )
    else:
        await message.answer("Выберите период расписания:", reply_markup=schedule_period_keyboard())


@router.message(ParentState.main_menu, F.text.in_(["📅 На сегодня", "📅 На неделю", "📅 На месяц"]))
async def parent_schedule_period(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    period_map = {"📅 На сегодня": 1, "📅 На неделю": 7, "📅 На месяц": 30}
    days = period_map[message.text]

    student_id = user.student_id or user.id
    schedule = get_schedule(student_id, limit_days=days)

    if not schedule:
        await message.answer("📭 Расписание на этот период пусто.", reply_markup=parent_main_keyboard())
        return

    lines = [f"📚 <b>Расписание ({message.text.replace('📅 ', '')}):</b>\n"]
    current_date = None
    for lesson in schedule:
        day_str = lesson.date_time.strftime("%d.%m (%A)")
        if day_str != current_date:
            current_date = day_str
            lines.append(f"\n📅 <b>{day_str}</b>")
        lines.append(
            f"  🕐 {lesson.date_time.strftime('%H:%M')} — {lesson.lesson_name}\n"
            f"     📍 {lesson.location} | 👤 {lesson.teacher}"
        )
    await message.answer("\n".join(lines), reply_markup=parent_main_keyboard(), parse_mode="HTML")


# ========== Финансы ==========

@router.message(ParentState.main_menu, F.text == "💰 Финансы")
async def parent_finance(message: Message, state: FSMContext):
    photo = get_photo("finance")
    user = get_user(message.from_user.id)
    student_id = user.student_id or user.id

    debts = get_debts(student_id)
    payments = get_payments_history(student_id)

    text = "💰 <b>Финансовый блок</b>\n\n"

    if debts:
        text += "❗ <b>Задолженности:</b>\n"
        for d in debts:
            text += f"  • {d.amount:,.0f} ₽ — {d.date.strftime('%d.%m.%Y')}\n"
    else:
        text += "✅ Задолженностей нет.\n"

    text += "\n📋 <b>История платежей:</b>\n"
    for p in payments:
        icon = "✅" if p.status == "paid" else "❗"
        text += f"  {icon} {p.amount:,.0f} ₽ — {p.date.strftime('%d.%m.%Y')}\n"

    if photo:
        await message.answer_photo(photo=photo, caption=text, reply_markup=parent_main_keyboard(), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=parent_main_keyboard(), parse_mode="HTML")


# ========== Мероприятия ==========

@router.message(ParentState.main_menu, F.text == "🎉 Мероприятия")
async def parent_events(message: Message, state: FSMContext):
    photo = get_photo("events")
    user = get_user(message.from_user.id)
    events = get_events()
    if not events:
        await message.answer("📭 Предстоящих мероприятий нет.", reply_markup=parent_main_keyboard())
        return

    if photo:
        await message.answer_photo(
            photo=photo,
            caption="🎉 <b>Предстоящие мероприятия:</b>\nНажмите на мероприятие для подробностей.",
            reply_markup=events_inline_keyboard(events, user.id),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "🎉 <b>Предстоящие мероприятия:</b>\nНажмите на мероприятие для подробностей.",
            reply_markup=events_inline_keyboard(events, user.id),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("event_"))
async def event_detail(callback: CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[1])
    e = get_event(event_id)
    user = get_user(callback.from_user.id)
    already = is_registered_for_event(user.id, event_id)

    registered_count = len(e.registered_users.split(",")) if e.registered_users else 0
    text = (
        f"🎉 <b>{e.title}</b>\n\n"
        f"📝 {e.description}\n"
        f"📅 {e.date.strftime('%d.%m.%Y %H:%M')}\n"
        f"👥 Записалось: {registered_count} чел."
    )
    await callback.message.edit_text(text,
                                     reply_markup=event_register_keyboard(event_id, already),
                                     parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("reg_"))
async def register_event(callback: CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[1])
    user = get_user(callback.from_user.id)
    e = get_event(event_id)

    if register_for_event(user.id, event_id):
        try:
            from aiogram import Bot
            bot = callback.bot
            tg_link = f"tg://user?id={callback.from_user.id}"
            await bot.send_message(
                ADMIN_ID,
                f"📌 <b>Регистрация на мероприятие</b>\n\n"
                f"Пользователь: <a href='{tg_link}'>{user.full_name}</a>\n"
                f"Мероприятие: {e.title} ({e.date.strftime('%d.%m.%Y')})",
                parse_mode="HTML",
            )
        except Exception:
            pass
        await callback.answer("✅ Вы записаны на мероприятие!")
        await callback.message.edit_reply_markup(
            reply_markup=event_register_keyboard(event_id, True))
    else:
        await callback.answer("Вы уже записаны.")


@router.callback_query(F.data == "events_list")
async def back_to_events(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    events = get_events()
    await callback.message.edit_text(
        "🎉 <b>Предстоящие мероприятия:</b>",
        reply_markup=events_inline_keyboard(events, user.id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "already_registered")
async def already_registered(callback: CallbackQuery):
    await callback.answer("Вы уже записаны на это мероприятие.")


# ========== Успеваемость ==========

@router.message(ParentState.main_menu, F.text == "📊 Успеваемость")
async def parent_grades(message: Message, state: FSMContext):
    photo = get_photo("grades")
    user = get_user(message.from_user.id)
    student_id = user.student_id or user.id
    grades = get_grades(student_id)

    if not grades:
        await message.answer("📭 Оценки пока не выставлены.", reply_markup=parent_main_keyboard())
        return

    avg = calculate_average_grade(student_id)
    text = f"📊 <b>Успеваемость</b>\n\nСредний балл: <b>{avg}</b>\n\n"
    for g in grades:
        stars = "⭐" * round(g.grade)
        text += (
            f"📚 <b>{g.subject}</b>: {g.grade} {stars}\n"
            f"   💬 {g.teacher_feedback}\n"
            f"   📅 {g.date.strftime('%d.%m.%Y')}\n\n"
        )

    if photo:
        await message.answer_photo(photo=photo, caption=text, reply_markup=parent_main_keyboard(), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=parent_main_keyboard(), parse_mode="HTML")


# ========== Запрос обратной связи от учителя ==========

@router.message(ParentState.main_menu, F.text == "👨‍🏫 Учитель")
async def parent_teacher(message: Message, state: FSMContext):
    photo = get_photo("teacher")
    await state.set_state(ParentState.waiting_for_feedback_request)
    if photo:
        await message.answer_photo(
            photo=photo,
            caption="✍️ Напишите ваш запрос обратной связи от преподавателя:",
            reply_markup=back_keyboard(),
        )
    else:
        await message.answer(
            "✍️ Напишите ваш запрос обратной связи от преподавателя:",
            reply_markup=back_keyboard(),
        )


@router.message(ParentState.waiting_for_feedback_request, F.text == "🔙 Назад")
async def parent_teacher_back(message: Message, state: FSMContext):
    await state.set_state(ParentState.main_menu)
    await message.answer("Главное меню:", reply_markup=parent_main_keyboard())


@router.message(ParentState.waiting_for_feedback_request)
async def parent_teacher_send(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    tg_link = f"tg://user?id={message.from_user.id}"
    try:
        await message.bot.send_message(
            ADMIN_ID,
            f"📩 <b>Запрос обратной связи от родителя</b>\n\n"
            f"От: <a href='{tg_link}'>{user.full_name}</a>\n"
            f"Сообщение: {message.text}",
            parse_mode="HTML",
        )
        await message.answer("✅ Запрос отправлен преподавателю!", reply_markup=parent_main_keyboard())
    except Exception:
        await message.answer("❌ Не удалось отправить запрос. Попробуйте позже.",
                             reply_markup=parent_main_keyboard())
    await state.set_state(ParentState.main_menu)


# ========== Справки ==========

@router.message(ParentState.main_menu, F.text == "📄 Справки")
async def parent_certificates(message: Message, state: FSMContext):
    photo = get_photo("certificates")
    await state.set_state(ParentState.waiting_for_certificate_type)
    if photo:
        await message.answer_photo(
            photo=photo,
            caption="Выберите тип справки:",
            reply_markup=certificate_keyboard()
        )
    else:
        await message.answer("Выберите тип справки:", reply_markup=certificate_keyboard())


@router.message(ParentState.waiting_for_certificate_type, F.text == "🔙 Назад")
async def cert_back(message: Message, state: FSMContext):
    await state.set_state(ParentState.main_menu)
    await message.answer("Главное меню:", reply_markup=parent_main_keyboard())


@router.message(ParentState.waiting_for_certificate_type,
                F.text.in_(["📋 Справка об обучении", "💼 Справка для налогового вычета"]))
async def cert_type_selected(message: Message, state: FSMContext):
    await state.update_data(cert_type=message.text)
    await state.set_state(ParentState.waiting_for_certificate_name)
    await message.answer("Введите ваше ФИО для оформления справки:", reply_markup=back_keyboard())


@router.message(ParentState.waiting_for_certificate_name, F.text == "🔙 Назад")
async def cert_name_back(message: Message, state: FSMContext):
    await state.set_state(ParentState.waiting_for_certificate_type)
    await message.answer("Выберите тип справки:", reply_markup=certificate_keyboard())


@router.message(ParentState.waiting_for_certificate_name)
async def cert_name_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    cert_type = data.get("cert_type", "Справка")
    full_name = message.text.strip()
    user = get_user(message.from_user.id)
    tg_link = f"tg://user?id={message.from_user.id}"

    try:
        await message.bot.send_message(
            ADMIN_ID,
            f"📄 <b>Заказ справки</b>\n\n"
            f"Тип: {cert_type}\n"
            f"ФИО: {full_name}\n"
            f"Запросил: <a href='{tg_link}'>{user.full_name}</a>",
            parse_mode="HTML",
        )
        await message.answer("✅ Запрос на справку отправлен!", reply_markup=parent_main_keyboard())
    except Exception:
        await message.answer("❌ Ошибка при отправке запроса.", reply_markup=parent_main_keyboard())
    await state.set_state(ParentState.main_menu)


# ========== Новости ==========

@router.message(ParentState.main_menu, F.text == "📰 Новости")
async def parent_news(message: Message, state: FSMContext):
    photo = get_photo("news")
    news = get_recent_news()
    if not news:
        await message.answer("📭 Новостей пока нет.", reply_markup=parent_main_keyboard())
        return
    for n in reversed(news):
        if photo:
            await message.answer_photo(
                photo=photo,
                caption=f"📰 {n.date.strftime('%d.%m.%Y')}\n\n{n.text}",
                reply_markup=parent_main_keyboard(),
            )
        else:
            await message.answer(
                f"📰 {n.date.strftime('%d.%m.%Y')}\n\n{n.text}",
                reply_markup=parent_main_keyboard()
            )


# ========== Запись на встречу ==========

@router.message(ParentState.main_menu, F.text == "📅 Встреча")
async def parent_meeting(message: Message, state: FSMContext):
    photo = get_photo("meeting")
    await state.set_state(ParentState.waiting_for_meeting_teacher)
    if photo:
        await message.answer_photo(
            photo=photo,
            caption="📅 Запись на индивидуальную встречу.\n\nУкажите имя преподавателя, с которым хотите встретиться:",
            reply_markup=back_keyboard(),
        )
    else:
        await message.answer(
            "📅 Запись на индивидуальную встречу.\n\nУкажите имя преподавателя, с которым хотите встретиться:",
            reply_markup=back_keyboard(),
        )


@router.message(ParentState.waiting_for_meeting_teacher, F.text == "🔙 Назад")
async def meeting_teacher_back(message: Message, state: FSMContext):
    await state.set_state(ParentState.main_menu)
    await message.answer("Главное меню:", reply_markup=parent_main_keyboard())


@router.message(ParentState.waiting_for_meeting_teacher)
async def meeting_teacher_entered(message: Message, state: FSMContext):
    await state.update_data(meeting_teacher=message.text.strip())
    await state.set_state(ParentState.waiting_for_meeting_datetime)
    await message.answer(
        "Укажите удобные дату и время (например: 15.05.2026 14:00):",
        reply_markup=back_keyboard(),
    )


@router.message(ParentState.waiting_for_meeting_datetime, F.text == "🔙 Назад")
async def meeting_dt_back(message: Message, state: FSMContext):
    await state.set_state(ParentState.waiting_for_meeting_teacher)
    await message.answer("Укажите имя преподавателя:", reply_markup=back_keyboard())


@router.message(ParentState.waiting_for_meeting_datetime)
async def meeting_datetime_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    teacher = data.get("meeting_teacher")
    datetime_str = message.text.strip()
    user = get_user(message.from_user.id)
    tg_link = f"tg://user?id={message.from_user.id}"

    try:
        await message.bot.send_message(
            ADMIN_ID,
            f"📅 <b>Запрос на встречу</b>\n\n"
            f"От: <a href='{tg_link}'>{user.full_name}</a>\n"
            f"Преподаватель: {teacher}\n"
            f"Желаемое время: {datetime_str}",
            parse_mode="HTML",
        )
        await message.answer("✅ Запрос на встречу отправлен!", reply_markup=parent_main_keyboard())
    except Exception:
        await message.answer("❌ Ошибка при отправке запроса.", reply_markup=parent_main_keyboard())
    await state.set_state(ParentState.main_menu)


# ========== Помощь ==========

@router.message(ParentState.main_menu, F.text == "❓ Помощь")
async def parent_help(message: Message, state: FSMContext):
    photo = get_photo("help")
    help_text = (
        "❓ <b>Помощь Movavik</b>\n\n"
        "📚 <b>Расписание</b> — просмотр занятий на день/неделю/месяц\n"
        "💰 <b>Финансы</b> — задолженности и история платежей\n"
        "🎉 <b>Мероприятия</b> — анонсы и регистрация\n"
        "📊 <b>Успеваемость</b> — оценки, отзывы, средний балл\n"
        "📄 <b>Справки</b> — заказ документов (обучение/налоговый вычет)\n"
        "👨‍🏫 <b>Учитель</b> — запрос обратной связи от преподавателя\n"
        "📅 <b>Встреча</b> — запись на индивидуальную встречу\n\n"
        "📌 По всем вопросам: @school_movavi"
    )
    if photo:
        await message.answer_photo(
            photo=photo,
            caption=help_text,
            reply_markup=parent_main_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(help_text, reply_markup=parent_main_keyboard(), parse_mode="HTML")