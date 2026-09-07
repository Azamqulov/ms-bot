from datetime import datetime, timezone
from typing import Optional, Dict, Any
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.services.test_service import (
    get_or_create_user,
    get_default_test,
    get_active_attempt,
    start_new_attempt,
    get_question_by_order,
    get_user_answers_map,
    save_answer,
    finish_attempt,
)
from bot.services.report_service import generate_result_report, generate_teacher_notification
from bot.database.session import async_session_maker
from bot.database.models import Test, User
from sqlalchemy import select
from bot.core.latex import clean_latex
from bot.keyboards.inline import (
    get_question_keyboard,
    get_questions_grid_keyboard,
    get_finish_confirmation_keyboard,
    get_restart_keyboard,
)
from bot.states.test_state import TestSessionState

router = Router(name="test_runner")


def format_remaining_time(started_at: datetime, time_limit_min: int) -> str:
    """Qolgan vaqtni daqiqa va soniyalarda hisoblash"""
    now = datetime.now(timezone.utc)
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)

    elapsed_sec = int((now - started_at).total_seconds())
    total_sec = time_limit_min * 60
    remaining_sec = max(0, total_sec - elapsed_sec)

    hours = remaining_sec // 3600
    mins = (remaining_sec % 3600) // 60
    return f"{hours:02d}:{mins:02d}"


async def build_question_display(attempt_id: int, test_id: int, order_no: int, started_at: datetime, time_limit_min: int):
    """Bitta savol uchun matn va klaviaturani tayyorlash"""
    question = await get_question_by_order(test_id, order_no)
    if not question:
        return None, None

    answers_map = await get_user_answers_map(attempt_id)
    rem_time = format_remaining_time(started_at, time_limit_min)

    # Matnni yig'ish
    header = (
        f"📝 <b>SAVOL {question.order_no} / 45</b>\n"
        f"📌 <b>Bo'lim:</b> {question.section} | ⏳ <b>Qolgan vaqt:</b> {rem_time}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n\n"
    )

    body = ""
    user_answer = answers_map.get(str(question.id))
    subpart_answers = {
        "a": answers_map.get(f"{question.id}_a"),
        "b": answers_map.get(f"{question.id}_b"),
    }

    cleaned_text = clean_latex(question.text)

    if question.type == "Y-1":
        body += f"{cleaned_text}\n\n"
        if question.options:
            body += "<b>Variantlar:</b>\n"
            for opt_key in ["A", "B", "C", "D"]:
                val = clean_latex(question.options.get(opt_key, ""))
                mark = "👉 " if user_answer == opt_key else "  "
                body += f"{mark}<b>{opt_key})</b> {val}\n"
        if user_answer:
            body += f"\n<i>Siz tanlagan variant:</i> <b>{user_answer}</b>"

    elif question.type == "GROUPED":
        if question.group:
            body += f"📖 {clean_latex(question.group.shared_context_text)}\n\n"
        body += f"<b>{cleaned_text}</b>\n\n"
        if user_answer:
            body += f"\n<i>Siz tanlagan variant:</i> <b>{user_answer}</b>"

    elif question.type == "O":
        body += f"{cleaned_text}\n\n"
        body += "<b>Siz kiritgan javoblar:</b>\n"
        body += f"• a) bandi: <code>{subpart_answers.get('a') or 'Kiritilmagan'}</code>\n"
        body += f"• b) bandi: <code>{subpart_answers.get('b') or 'Kiritilmagan'}</code>\n\n"
        body += "<i>Javob kiritish uchun quyidagi '✍️ a) yoki b)' tugmasini bosing.</i>"

    keyboard = get_question_keyboard(
        question_type=question.type,
        order_no=order_no,
        total_questions=45,
        user_answer=user_answer,
        subpart_answers=subpart_answers,
    )

    return header + body, keyboard


from bot.services.admin_service import get_test_by_code
from bot.states.admin_state import UserCodeEntryState
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_code_prompt_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="🚀 STANDART testni boshlash", callback_data="start_by_code:STANDART")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.message(F.text.in_(["📝 Test topshirish", "📝 Botda topshirish"]))
@router.callback_query(F.data == "start_test_prompt")
async def prompt_test_code_entry(event: Message | CallbackQuery, state: FSMContext):
    user_obj = event.from_user
    message = event if isinstance(event, Message) else event.message

    user = await get_or_create_user(
        telegram_id=user_obj.id,
        full_name=user_obj.full_name,
        username=user_obj.username,
    )

    # Agar allaqachon faol test bo'lsa, to'g'ridan-to'g'ri o'sha testga o'tamiz
    active_attempt = await get_active_attempt(user.id)
    if active_attempt:
        test = await get_default_test()
        time_limit = test.time_limit_min if test else 150
        await state.set_state(TestSessionState.testing)
        await state.update_data(attempt_id=active_attempt.id, test_id=active_attempt.test_id, current_order=1)

        text, kb = await build_question_display(
            attempt_id=active_attempt.id,
            test_id=active_attempt.test_id,
            order_no=1,
            started_at=active_attempt.started_at,
            time_limit_min=time_limit,
        )
        if isinstance(event, CallbackQuery):
            await event.answer()
            await message.edit_text(text, reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb)
        return

    # Yangi test boshlash uchun kod so'rash
    await state.set_state(UserCodeEntryState.waiting_test_code)
    prompt_text = (
        "🔑 <b>TEST KODINI KIRITING:</b>\n\n"
        "• Agar admingiz yoki o'qituvchingiz sizga maxsus test kodi bergan bo'lsa, kodni yozib yuboring (masalan: <code>MATH-01</code>);\n"
        "• Rasmiy 45 talik standart mock testni topshirish uchun quyidagi tugmani bosing yoki <code>STANDART</code> deb yozing."
    )
    if isinstance(event, CallbackQuery):
        await event.answer()
        await message.edit_text(prompt_text, reply_markup=get_code_prompt_keyboard())
    else:
        await message.answer(prompt_text, reply_markup=get_code_prompt_keyboard())


@router.callback_query(F.data.startswith("start_by_code:"))
async def handle_start_by_code_callback(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split(":")[1]
    await begin_test_with_code(callback.from_user, callback.message, state, code, is_edit=True)
    await callback.answer()


@router.message(UserCodeEntryState.waiting_test_code)
async def handle_user_typed_test_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    await begin_test_with_code(message.from_user, message, state, code, is_edit=False)


async def begin_test_with_code(user_obj, message: Message, state: FSMContext, code: str, is_edit: bool = False):
    """Kiritilgan kod bo'yicha testni qidirish va boshlash"""
    test = await get_test_by_code(code)
    if not test and code == "STANDART":
        test = await get_default_test()

    if not test:
        reply = (
            f"❌ <b>'{code}' kodli test topilmadi!</b>\n\n"
            f"Iltimos, kodni to'g'ri kiritganingizni tekshiring yoki <b>STANDART</b> tugmasini bosing:"
        )
        if is_edit:
            await message.edit_text(reply, reply_markup=get_code_prompt_keyboard())
        else:
            await message.answer(reply, reply_markup=get_code_prompt_keyboard())
        return

    user = await get_or_create_user(
        telegram_id=user_obj.id,
        full_name=user_obj.full_name,
        username=user_obj.username,
    )

    new_attempt = await start_new_attempt(user.id, test.id)

    await state.set_state(TestSessionState.testing)
    await state.update_data(attempt_id=new_attempt.id, test_id=test.id, current_order=1)

    text, kb = await build_question_display(
        attempt_id=new_attempt.id,
        test_id=test.id,
        order_no=1,
        started_at=new_attempt.started_at,
        time_limit_min=test.time_limit_min,
    )

    intro = (
        f"🎯 <b>Test boshlandi: {test.title}</b>\n"
        f"🔑 <i>Kodi:</i> <code>{test.code}</code> | ⏱ <i>Vaqt:</i> {test.time_limit_min} daqiqa\n\n"
    )
    if is_edit:
        await message.edit_text(intro + text, reply_markup=kb)
    else:
        await message.answer(intro + text, reply_markup=kb)


@router.callback_query(F.data.startswith("nav:"))
async def handle_navigation(callback: CallbackQuery, state: FSMContext):
    data_parts = callback.data.split(":")
    order_no = int(data_parts[1])

    state_data = await state.get_data()
    attempt_id = state_data.get("attempt_id")
    test_id = state_data.get("test_id")

    if not attempt_id or not test_id:
        user = await get_or_create_user(callback.from_user.id, callback.from_user.full_name)
        active_attempt = await get_active_attempt(user.id)
        if not active_attempt:
            await callback.answer("⚠️ Faol test sessiyasi topilmadi.", show_alert=True)
            return
        attempt_id = active_attempt.id
        test_id = active_attempt.test_id
        await state.update_data(attempt_id=attempt_id, test_id=test_id)

    test = await get_default_test()
    time_limit = test.time_limit_min if test else 150

    await state.update_data(current_order=order_no)
    text, kb = await build_question_display(
        attempt_id=attempt_id,
        test_id=test_id,
        order_no=order_no,
        started_at=datetime.now(timezone.utc), # mock display vaqt
        time_limit_min=time_limit,
    )

    await callback.answer()
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data.startswith("ans:"))
async def handle_choice_answer(callback: CallbackQuery, state: FSMContext):
    # ans:order_no:option (masalan ans:1:B)
    _, order_str, option = callback.data.split(":")
    order_no = int(order_str)

    state_data = await state.get_data()
    attempt_id = state_data.get("attempt_id")
    test_id = state_data.get("test_id")

    if not attempt_id or not test_id:
        user = await get_or_create_user(callback.from_user.id, callback.from_user.full_name)
        active_attempt = await get_active_attempt(user.id)
        if not active_attempt:
            await callback.answer("⚠️ Faol test topilmadi.", show_alert=True)
            return
        attempt_id = active_attempt.id
        test_id = active_attempt.test_id

    question = await get_question_by_order(test_id, order_no)
    if not question:
        await callback.answer("Savol topilmadi.")
        return

    is_correct = (option == question.correct_answer)
    await save_answer(
        attempt_id=attempt_id,
        question_id=question.id,
        user_answer=option,
        is_correct=is_correct,
        sub_part_label=None,
    )

    await callback.answer(f"Tanlandi: {option}")

    # Agar 45-savol bo'lmasa, avtomatik keyingi savolga o'tish qulay UX beradi
    next_order = order_no + 1 if order_no < 45 else order_no
    await state.update_data(current_order=next_order)

    test = await get_default_test()
    time_limit = test.time_limit_min if test else 150

    text, kb = await build_question_display(
        attempt_id=attempt_id,
        test_id=test_id,
        order_no=next_order,
        started_at=datetime.now(timezone.utc),
        time_limit_min=time_limit,
    )

    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data.startswith("grid:"))
async def handle_grid_view(callback: CallbackQuery, state: FSMContext):
    current_order = int(callback.data.split(":")[1])
    state_data = await state.get_data()
    attempt_id = state_data.get("attempt_id")

    # Javob berilgan savollarni aniqlash
    answers_map = await get_user_answers_map(attempt_id) if attempt_id else {}
    test = await get_default_test()
    if not test:
        await callback.answer()
        return

    # Qaysi order_no larda javob bor
    answered_orders = set()
    for o_no in range(1, 46):
        q = await get_question_by_order(test.id, o_no)
        if q:
            if q.type in ("Y-1", "GROUPED"):
                if str(q.id) in answers_map:
                    answered_orders.add(o_no)
            elif q.type == "O":
                if f"{q.id}_a" in answers_map or f"{q.id}_b" in answers_map:
                    answered_orders.add(o_no)

    text = (
        "📋 <b>BARCHA SAVOLLAR XARITASI</b>\n\n"
        "Quyidagi katakchalardan istalgan savol raqamini bosib to'g'ridan-to'g'ri unga o'tishingiz mumkin:\n"
        "• 📍 — Siz turgan joriy savol\n"
        "• ✅ — Javob berilgan savol\n"
        "• Son — Hali javob berilmagan savol\n"
    )
    kb = get_questions_grid_keyboard(
        current_order=current_order,
        total_questions=45,
        answered_orders=answered_orders
    )
    await callback.answer()
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data == "confirm_finish")
async def handle_confirm_finish(callback: CallbackQuery):
    text = (
        "⚠️ <b>DIQQAT! TESTNI YAKUNLASH</b>\n\n"
        "Haqiqatan ham testni yakunlamoqchimisiz?\n\n"
        "<i>Eslatma: Javob berilmagan savollar xato deb hisoblanadi va "
        "RASH modeli bo'yicha umumiy ballingiz hisoblab chiqariladi.</i>"
    )
    kb = get_finish_confirmation_keyboard()
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "cancel_finish")
async def handle_cancel_finish(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    order_no = state_data.get("current_order", 1)
    attempt_id = state_data.get("attempt_id")
    test_id = state_data.get("test_id")

    test = await get_default_test()
    time_limit = test.time_limit_min if test else 150

    text, kb = await build_question_display(
        attempt_id=attempt_id,
        test_id=test_id,
        order_no=order_no,
        started_at=datetime.now(timezone.utc),
        time_limit_min=time_limit,
    )
    await callback.answer("Davom etamiz!")
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "do_finish")
async def handle_do_finish(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    attempt_id = state_data.get("attempt_id")

    user = await get_or_create_user(callback.from_user.id, callback.from_user.full_name)
    if not attempt_id:
        active = await get_active_attempt(user.id)
        if active:
            attempt_id = active.id

    if not attempt_id:
        await callback.answer("⚠️ Yakunlash uchun faol test topilmadi.", show_alert=True)
        return

    await callback.answer("Natijalar RASH modeli asosida hisoblanmoqda...")

    # Natijani hisoblash
    attempt, rasch_result = await finish_attempt(attempt_id)
    await state.clear()

    report_text = generate_result_report(user, attempt, rasch_result)
    kb = get_restart_keyboard()

    await callback.message.edit_text(report_text, reply_markup=kb)

    # Test yaratgan odamga natijani yuborish
    try:
        async with async_session_maker() as session:
            t_stmt = select(Test).where(Test.id == attempt.test_id)
            t_res = await session.execute(t_stmt)
            test_obj = t_res.scalar_one_or_none()
            if test_obj and test_obj.created_by_user_id:
                c_user = await session.get(User, test_obj.created_by_user_id)
                if c_user and c_user.telegram_id and c_user.telegram_id != user.telegram_id:
                    teacher_text = generate_teacher_notification(
                        student=user,
                        test_title=test_obj.title,
                        test_code=test_obj.code,
                        attempt=attempt,
                        rasch_result=rasch_result
                    )
                    await callback.bot.send_message(
                        chat_id=c_user.telegram_id,
                        text=teacher_text,
                        parse_mode="HTML"
                    )
    except Exception as e:
        pass
