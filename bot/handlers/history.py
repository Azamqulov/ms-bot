from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.services.test_service import get_or_create_user, get_user_attempts_history
from bot.services.report_service import generate_history_report
from bot.keyboards.inline import get_restart_keyboard

router = Router(name="history")


@router.message(F.text == "📊 Natijalarim")
@router.message(Command("natijalarim"))
@router.callback_query(F.data == "show_my_history")
async def show_history(event: Message | CallbackQuery):
    user_obj = event.from_user
    message = event if isinstance(event, Message) else event.message

    user = await get_or_create_user(
        telegram_id=user_obj.id,
        full_name=user_obj.full_name,
        username=user_obj.username,
    )

    attempts = await get_user_attempts_history(user.id)
    report_text = generate_history_report(attempts)

    if isinstance(event, CallbackQuery):
        await event.answer()
        await message.answer(report_text, reply_markup=get_restart_keyboard())
    else:
        await message.answer(report_text, reply_markup=get_restart_keyboard())
