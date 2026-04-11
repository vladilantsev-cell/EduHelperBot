from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from states import AuthState, ParentState, StudentState, AdminState
from keyboards import role_keyboard, parent_main_keyboard, student_main_keyboard, admin_main_keyboard
from database import get_user_by_credentials, update_user_telegram_id, get_user
from config import ADMIN_ID
from photo_utils import get_photo, get_bot_avatar

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    # Отправляем аватарку бота
    avatar = get_bot_avatar()
    await message.answer_photo(
        photo=avatar,
        caption="🤖 <b>Movavik</b> — ваш помощник в IT Школе Movavi!\n\n"
                "Я помогу вам следить за расписанием, успеваемостью и мероприятиями.",
        parse_mode="HTML"
    )

    user = get_user(message.from_user.id)
    if user:
        if user.role == "parent":
            await state.set_state(ParentState.main_menu)
            photo = get_photo("welcome_parent")
            if photo:
                await message.answer_photo(
                    photo=photo,
                    caption=f"👋 С возвращением, <b>{user.full_name}</b>!",
                    reply_markup=parent_main_keyboard(),
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    f"👋 С возвращением, <b>{user.full_name}</b>!",
                    reply_markup=parent_main_keyboard(),
                    parse_mode="HTML"
                )
        elif user.role == "student":
            await state.set_state(StudentState.main_menu)
            photo = get_photo("welcome_student")
            if photo:
                await message.answer_photo(
                    photo=photo,
                    caption=f"👋 С возвращением, <b>{user.full_name}</b>!",
                    reply_markup=student_main_keyboard(),
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    f"👋 С возвращением, <b>{user.full_name}</b>!",
                    reply_markup=student_main_keyboard(),
                    parse_mode="HTML"
                )
        elif user.role == "admin":
            await state.set_state(AdminState.main_menu)
            photo = get_photo("welcome_admin")
            if photo:
                await message.answer_photo(
                    photo=photo,
                    caption="👋 Привет, Администратор!",
                    reply_markup=admin_main_keyboard(),
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    "👋 Привет, Администратор!",
                    reply_markup=admin_main_keyboard(),
                    parse_mode="HTML"
                )
        return

    await state.set_state(AuthState.waiting_for_role)
    await message.answer(
        "Выберите вашу роль:",
        reply_markup=role_keyboard(),
        parse_mode="HTML",
    )
# выбор роли

@router.message(AuthState.waiting_for_role, F.text.in_(["👨‍👩‍👧 Родитель", "🎓 Ученик"]))
async def choose_role(message: Message, state: FSMContext):
    role_map = {"👨‍👩‍👧 Родитель": "parent", "🎓 Ученик": "student"}
    role = role_map[message.text]
    await state.update_data(role=role)
    await state.set_state(AuthState.waiting_for_login)
    await message.answer("Введите ваш <b>логин</b>:", parse_mode="HTML")


# логин

@router.message(AuthState.waiting_for_login)
async def process_login(message: Message, state: FSMContext):
    await state.update_data(login=message.text.strip())
    await state.set_state(AuthState.waiting_for_password)
    await message.answer("Введите ваш <b>пароль</b>:", parse_mode="HTML")

# пароль

@router.message(AuthState.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    data = await state.get_data()
    login = data.get("login")
    password = message.text.strip()
    chosen_role = data.get("role")

    user = get_user_by_credentials(login, password)

    if not user:
        await message.answer("❌ Неверный логин или пароль. Попробуйте ещё раз или введите /start.")
        await state.set_state(AuthState.waiting_for_login)
        await message.answer("Введите ваш <b>логин</b>:", parse_mode="HTML")
        return

    if user.role != chosen_role:
        await message.answer(
            f"❌ Ваша роль в системе: <b>{_role_ru(user.role)}</b>, "
            f"а вы выбрали <b>{_role_ru(chosen_role)}</b>.\n"
            "Вернитесь к выбору роли через /start.",
            parse_mode="HTML",
        )
        await state.clear()
        return

    # Привязываем telegram_id
    update_user_telegram_id(user.id, message.from_user.id)
    await state.clear()

    if user.role == "parent":
        await state.set_state(ParentState.main_menu)
        await message.answer(f"✅ Авторизация успешна!\n\nДобро пожаловать, <b>{user.full_name}</b>!",
                             reply_markup=parent_main_keyboard(), parse_mode="HTML")
    elif user.role == "student":
        await state.set_state(StudentState.main_menu)
        await message.answer(f"✅ Авторизация успешна!\n\nДобро пожаловать, <b>{user.full_name}</b>!",
                             reply_markup=student_main_keyboard(), parse_mode="HTML")
    elif user.role == "admin":
        await state.set_state(AdminState.main_menu)
        await message.answer("✅ Авторизация успешна!\n\nДобро пожаловать, <b>Администратор</b>!",
                             reply_markup=admin_main_keyboard(), parse_mode="HTML")

# /admin — быстрый вход для ADMIN_ID

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав администратора.")
        return
    await state.clear()
    await state.set_state(AdminState.main_menu)
    await message.answer("🔑 Вы вошли как администратор.", reply_markup=admin_main_keyboard())

# /help

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "ℹ️ <b>Movavik — бот IT Школы Movavi</b>\n\n"
        "Доступные команды:\n"
        "/start — перезапустить / войти\n"
        "/help — помощь\n\n"
        "Используйте кнопки меню для навигации.",
        parse_mode="HTML",
    )

# универсальные кнопки

@router.message(F.text == "❓ Помощь")
async def help_text(message: Message):
    await message.answer(
        "ℹ️ <b>Помощь Movavik</b>\n\n"
        "Используйте кнопки меню для доступа к функциям бота.\n"
        "При проблемах с авторизацией напишите /start.",
        parse_mode="HTML",
    )

def _role_ru(role: str) -> str:
    return {"parent": "Родитель", "student": "Ученик", "admin": "Администратор"}.get(role, role)
