from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_user, create_user, update_user_student_id
from keyboards import get_main_keyboard

router = Router()


class AuthState(StatesGroup):
    waiting_for_role = State()
    waiting_for_login = State()
    waiting_for_password = State()


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id)

    if user:
        await state.clear()
        await message.answer(
            f"👋 С возвращением, {user.full_name}!",
            reply_markup=get_main_keyboard(user.role)
        )
    else:
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="👨‍👩‍👧 Родитель")],
                [types.KeyboardButton(text="🧑‍🎓 Ученик")]
            ],
            resize_keyboard=True
        )
        await message.answer(
            "👋 Привет! Я EduHelper - твой помощник!\n\nВыбери роль:",
            reply_markup=keyboard
        )
        await state.set_state(AuthState.waiting_for_role)


@router.message(AuthState.waiting_for_role, F.text.in_(["👨‍👩‍👧 Родитель", "🧑‍🎓 Ученик"]))
async def role_selected(message: types.Message, state: FSMContext):
    role_map = {"👨‍👩‍👧 Родитель": "parent", "🧑‍🎓 Ученик": "student"}
    await state.update_data(role=role_map[message.text])
    await message.answer("🔐 Введите логин:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AuthState.waiting_for_login)


@router.message(AuthState.waiting_for_login)
async def login_entered(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.answer("🔑 Введите пароль:")
    await state.set_state(AuthState.waiting_for_password)


@router.message(AuthState.waiting_for_password)
async def password_entered(message: types.Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("role")
    login = data.get("login")
    password = message.text

    user = get_user(message.from_user.id)

    if not user:
        full_name = "Ученик" if role == "student" else "Родитель"
        user = create_user(message.from_user.id, role, login, password, full_name)
        if role == "parent":
            update_user_student_id(message.from_user.id, user.id)

    await state.clear()
    await message.answer(
        f"✅ Добро пожаловать, {user.full_name}!",
        reply_markup=get_main_keyboard(role)
    )