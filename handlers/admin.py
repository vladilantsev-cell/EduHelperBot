from aiogram import Router, types
from aiogram.filters import Command

from config import ADMIN_ID

router = Router()


@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    """Админ-панель (только для админа)"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет доступа к этой команде")
        return

    await message.answer(
        "🔐 *Админ-панель*\n\n"
        "Бот работает в штатном режиме.\n"
        "Все запросы от пользователей приходят в этот чат.\n\n"
        "Доступные команды:\n"
        "/stats - статистика\n"
        "/broadcast - рассылка (в разработке)",
        parse_mode="Markdown"
    )


@router.message(Command("stats"))
async def admin_stats(message: types.Message):
    """Статистика (только для админа)"""
    if message.from_user.id != ADMIN_ID:
        return

    from database import Session, User, Event

    session = Session()
    users_count = session.query(User).count()
    events_count = session.query(Event).count()
    session.close()

    await message.answer(
        f"📊 *Статистика*\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"🎉 Мероприятий: {events_count}\n"
        f"🤖 Бот работает",
        parse_mode="Markdown"
    )