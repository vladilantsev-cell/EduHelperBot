from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import StudentState, AuthState
from keyboards import (
    student_main_keyboard, back_keyboard,
    schedule_period_keyboard,
    events_inline_keyboard, event_register_keyboard,
    shop_inline_keyboard, buy_inline_keyboard,
)
from database import (
    get_user, logout_user,
    get_schedule,
    get_events, get_event, register_for_event, is_registered_for_event, get_user_events,
    get_boost, get_transactions, spend_boost,
    get_shop_items, get_shop_item,
    get_grades, calculate_average_grade,
)
from config import ADMIN_ID
from photo_utils import get_photo

router = Router()

# ========== Выход ==========

@router.message(StudentState.main_menu, F.text == "🚪 Выйти")
async def student_logout(message: Message, state: FSMContext):
    logout_user(message.from_user.id)
    await state.clear()
    await state.set_state(AuthState.waiting_for_role)
    from keyboards import role_keyboard
    await message.answer("👋 Вы вышли из системы. Используйте /start для входа.",
                         reply_markup=role_keyboard())

# ========== Бусты и магазин ==========

@router.message(StudentState.main_menu, F.text == "⭐ Мои бусты")
async def student_boosts(message: Message, state: FSMContext):
    photo = get_photo("boosts")
    user = get_user(message.from_user.id)
    boosts = get_boost(user.id)
    transactions = get_transactions(user.id)

    text = f"⭐ <b>Movavi Boost</b>\n\nВаш баланс: <b>{boosts} 🪙</b>\n\n"
    text += "📋 <b>История транзакций:</b>\n"
    if transactions:
        for t in transactions:
            sign = "+" if t.amount > 0 else ""
            text += f"  {sign}{t.amount} 🪙 — {t.reason} ({t.date.strftime('%d.%m')})\n"
    else:
        text += "  Транзакций пока нет.\n"

    text += "\n🛍 Хотите потратить бусты в магазине? Нажмите кнопку ниже."

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Перейти в магазин", callback_data="shop_list")]
    ])

    if photo:
        await message.answer_photo(photo=photo, caption=text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "shop_list")
async def shop_list(callback: CallbackQuery, state: FSMContext):
    items = get_shop_items()
    if not items:
        await callback.answer("Магазин пуст.")
        return
    await callback.message.edit_text(
        "🛒 <b>Магазин Movavi Boost</b>\n\nВыберите товар:",
        reply_markup=shop_inline_keyboard(items),
        parse_mode="HTML",
    )
    await callback.answer()

@router.callback_query(F.data.startswith("shop_"))
async def shop_item_detail(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split("_")[1])
    item = get_shop_item(item_id)
    user = get_user(callback.from_user.id)
    boosts = get_boost(user.id)

    text = (
        f"🛍 <b>{item.name}</b>\n\n"
        f"📝 {item.description}\n"
        f"💰 Цена: <b>{item.price} 🪙</b>\n\n"
        f"Ваш баланс: {boosts} 🪙"
    )
    await callback.message.edit_text(text, reply_markup=buy_inline_keyboard(item_id),
                                     parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("buy_"))
async def buy_item(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split("_")[1])
    item = get_shop_item(item_id)
    user = get_user(callback.from_user.id)

    if spend_boost(user.id, item.price):
        await callback.answer("✅ Покупка совершена!")
        try:
            await callback.bot.send_message(
                ADMIN_ID,
                f"🛒 <b>Покупка в магазине</b>\n\n"
                f"Ученик: {user.full_name}\n"
                f"Товар: {item.name} ({item.price} 🪙)",
                parse_mode="HTML",
            )
        except Exception:
            pass
        await callback.message.edit_text(
            f"✅ Вы приобрели: <b>{item.name}</b>!\n\n"
            f"🏢 Забрать товар можно у администратора на <b>первом этаже</b>.\n"
            f"Администратор уже получил уведомление о вашей покупке.",
            parse_mode="HTML",
        )
    else:
        await callback.answer("❌ Недостаточно бустов!")

# ========== Мероприятия ==========

@router.message(StudentState.main_menu, F.text == "🎉 Мероприятия")
async def student_events(message: Message, state: FSMContext):
    photo = get_photo("events")
    user = get_user(message.from_user.id)
    events = get_events()
    if not events:
        await message.answer("📭 Предстоящих мероприятий нет.", reply_markup=student_main_keyboard())
        return

    my_events = get_user_events(user.id)
    my_ids = {e.id for e in my_events}

    text = "🎉 <b>Мероприятия</b>\n\n"
    if my_events:
        text += "📌 <b>Вы записаны:</b>\n"
        for e in my_events:
            text += f"  • {e.title} — {e.date.strftime('%d.%m.%Y')}\n"
        text += "\n"
    text += "Выберите мероприятие для регистрации:"

    if photo:
        await message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=events_inline_keyboard(events, user.id),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            text,
            reply_markup=events_inline_keyboard(events, user.id),
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("event_"))
async def student_event_detail(callback: CallbackQuery, state: FSMContext):
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
async def student_register_event(callback: CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[1])
    user = get_user(callback.from_user.id)
    e = get_event(event_id)

    if register_for_event(user.id, event_id):
        try:
            tg_link = f"tg://user?id={callback.from_user.id}"
            await callback.bot.send_message(
                ADMIN_ID,
                f"📌 <b>Регистрация на мероприятие</b>\n\n"
                f"Ученик: <a href='{tg_link}'>{user.full_name}</a>\n"
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
async def student_back_to_events(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    events = get_events()
    await callback.message.edit_text(
        "🎉 <b>Предстоящие мероприятия:</b>",
        reply_markup=events_inline_keyboard(events, user.id),
        parse_mode="HTML",
    )
    await callback.answer()

@router.callback_query(F.data == "already_registered")
async def student_already_registered(callback: CallbackQuery):
    await callback.answer("Вы уже записаны на это мероприятие.")

# ========== Расписание ==========

@router.message(StudentState.main_menu, F.text == "📚 Расписание")
async def student_schedule(message: Message, state: FSMContext):
    photo = get_photo("schedule")
    if photo:
        await message.answer_photo(
            photo=photo,
            caption="Выберите период:",
            reply_markup=schedule_period_keyboard()
        )
    else:
        await message.answer("Выберите период:", reply_markup=schedule_period_keyboard())

@router.message(StudentState.main_menu, F.text.in_(["📅 На сегодня", "📅 На неделю", "📅 На месяц"]))
async def student_schedule_period(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    period_map = {"📅 На сегодня": 1, "📅 На неделю": 7, "📅 На месяц": 30}
    days = period_map[message.text]
    schedule = get_schedule(user.id, limit_days=days)

    if not schedule:
        await message.answer("📭 Расписание на этот период пусто.", reply_markup=student_main_keyboard())
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
    await message.answer("\n".join(lines), reply_markup=student_main_keyboard(), parse_mode="HTML")

# ========== Материалы ==========

@router.message(StudentState.main_menu, F.text == "📖 Материалы")
async def student_materials(message: Message, state: FSMContext):
    photo = get_photo("materials")
    text = (
        "📖 <b>Учебные материалы</b>\n\n"
        "🔗 Электронные материалы: <a href='https://school.movavi.ru/materials'>school.movavi.ru/materials</a>\n"
        "📚 Библиотека ресурсов: <a href='https://school.movavi.ru/library'>school.movavi.ru/library</a>\n\n"
        "💡 Ссылки на конкретные уроки появятся в расписании."
    )
    if photo:
        await message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=student_main_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.answer(
            text,
            reply_markup=student_main_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )

# ========== Написать учителю ==========

@router.message(StudentState.main_menu, F.text == "👨‍🏫 Написать учителю")
async def student_message_teacher(message: Message, state: FSMContext):
    photo = get_photo("message")
    await state.set_state(StudentState.waiting_for_teacher_message)
    if photo:
        await message.answer_photo(
            photo=photo,
            caption="✍️ Напишите сообщение преподавателю.\nОно будет передано через администратора:",
            reply_markup=back_keyboard(),
        )
    else:
        await message.answer(
            "✍️ Напишите сообщение преподавателю.\nОно будет передано через администратора:",
            reply_markup=back_keyboard(),
        )

@router.message(StudentState.waiting_for_teacher_message, F.text == "🔙 Назад")
async def student_teacher_back(message: Message, state: FSMContext):
    await state.set_state(StudentState.main_menu)
    await message.answer("Главное меню:", reply_markup=student_main_keyboard())

@router.message(StudentState.waiting_for_teacher_message)
async def student_teacher_send(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    tg_link = f"tg://user?id={message.from_user.id}"
    try:
        await message.bot.send_message(
            ADMIN_ID,
            f"✉️ <b>Сообщение от ученика преподавателю</b>\n\n"
            f"От: <a href='{tg_link}'>{user.full_name}</a>\n"
            f"Сообщение: {message.text}",
            parse_mode="HTML",
        )
        await message.answer("✅ Сообщение отправлено!", reply_markup=student_main_keyboard())
    except Exception:
        await message.answer("❌ Ошибка при отправке сообщения.", reply_markup=student_main_keyboard())
    await state.set_state(StudentState.main_menu)

# ========== Помощь ==========

@router.message(StudentState.main_menu, F.text == "❓ Помощь")
async def student_help(message: Message, state: FSMContext):
    photo = get_photo("help")
    help_text = (
        "❓ <b>Помощь Movavik</b>\n\n"
        "⭐ <b>Мои бусты</b> — баланс, история транзакций и магазин поощрений\n"
        "🎉 <b>Мероприятия</b> — анонсы и регистрация\n"
        "📚 <b>Расписание</b> — просмотр занятий на день/неделю/месяц\n"
        "📖 <b>Материалы</b> — ссылки на учебные ресурсы\n"
        "👨‍🏫 <b>Написать учителю</b> — отправить сообщение преподавателю\n\n"
        "📌 По всем вопросам: @school_movavi"
    )
    if photo:
        await message.answer_photo(
            photo=photo,
            caption=help_text,
            reply_markup=student_main_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(help_text, reply_markup=student_main_keyboard(), parse_mode="HTML")