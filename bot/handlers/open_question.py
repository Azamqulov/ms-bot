from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states.test_state import TestSessionState
from bot.keyboards.reply import get_cancel_keyboard, get_main_menu_keyboard
from bot.services.test_service import (
    get_or_create_user,
    get_active_attempt,
    get_question_by_order,
    save_answer,
    get_default_test,
)
from bot.core.validator import check_open_answer, parse_subparts_input
from bot.handlers.test_runner import build_question_display
from datetime import datetime, timezone

router = Router(name="open_question")


@router.callback_query(F.data.startswith("open_input:"))
async def prompt_open_answer(callback: CallbackQuery, state: FSMContext):
    # open_input:order_no:subpart (masalan open_input:36:a)
    _, order_str, subpart = callback.data.split(":")
    order_no = int(order_str)

    await state.set_state(TestSessionState.waiting_open_answer)
    await state.update_data(current_order=order_no, target_subpart=subpart)

    prompt = (
        f"✍️ <b>{order_no}-savolning {subpart}) bandi uchun javobingizni kiriting:</b>\n\n"
        f"<i>Masalan:</i> <code>12</code>, <code>-3.5</code> yoki <code>1/2</code>\n\n"
        f"💡 Agar ikkala bandga birdan javob bermoqchi bo'lsangiz: "
        f"<code>a) 3 b) -1</code> ko'rinishida ham yozishingiz mumkin."
    )
    await callback.answer()
    await callback.message.answer(prompt, reply_markup=get_cancel_keyboard())


@router.message(TestSessionState.waiting_open_answer, F.text == "❌ Bekor qilish / Orqaga")
async def cancel_open_input(message: Message, state: FSMContext):
    state_data = await state.get_data()
    order_no = state_data.get("current_order", 36)
    attempt_id = state_data.get("attempt_id")
    test_id = state_data.get("test_id")

    await state.set_state(TestSessionState.testing)

    test = await get_default_test()
    time_limit = test.time_limit_min if test else 150

    text, kb = await build_question_display(
        attempt_id=attempt_id,
        test_id=test_id,
        order_no=order_no,
        started_at=datetime.now(timezone.utc),
        time_limit_min=time_limit,
    )

    await message.answer("Joriy savolga qaytdik:", reply_markup=get_main_menu_keyboard())
    await message.answer(text, reply_markup=kb)


@router.message(TestSessionState.waiting_open_answer)
async def process_open_answer(message: Message, state: FSMContext):
    user_input = message.text.strip()
    state_data = await state.get_data()
    order_no = state_data.get("current_order", 36)
    target_subpart = state_data.get("target_subpart", "a")
    attempt_id = state_data.get("attempt_id")
    test_id = state_data.get("test_id")

    if not attempt_id or not test_id:
        user = await get_or_create_user(message.from_user.id, message.from_user.full_name)
        active = await get_active_attempt(user.id)
        if not active:
            await message.answer("⚠️ Faol test topilmadi.", reply_markup=get_main_menu_keyboard())
            await state.clear()
            return
        attempt_id = active.id
        test_id = active.test_id

    question = await get_question_by_order(test_id, order_no)
    if not question or not question.sub_parts:
        await message.answer("Savol topilmadi.", reply_markup=get_main_menu_keyboard())
        await state.clear()
        return

    # Foydalanuvchi "a) ... b) ..." shaklida birdan kiritgan bo'lishi mumkin
    parsed_parts = parse_subparts_input(user_input)

    subparts_dict = {sp["label"]: sp for sp in question.sub_parts}

    saved_info = []

    if parsed_parts:
        # Ikkala qismdan biri yoki ikkalasi topildi
        for label, val in parsed_parts.items():
            if label in subparts_dict:
                correct_val = subparts_dict[label].get("correct_answer", "")
                is_correct = check_open_answer(val, correct_val)
                await save_answer(
                    attempt_id=attempt_id,
                    question_id=question.id,
                    user_answer=val,
                    is_correct=is_correct,
                    sub_part_label=label,
                )
                saved_info.append(f"{label}) {val}")
    else:
        # Bitta target_subpart uchun kiritilgan
        correct_val = subparts_dict.get(target_subpart, {}).get("correct_answer", "")
        is_correct = check_open_answer(user_input, correct_val)
        await save_answer(
            attempt_id=attempt_id,
            question_id=question.id,
            user_answer=user_input,
            is_correct=is_correct,
            sub_part_label=target_subpart,
        )
        saved_info.append(f"{target_subpart}) {user_input}")

    await state.set_state(TestSessionState.testing)

    test = await get_default_test()
    time_limit = test.time_limit_min if test else 150

    text, kb = await build_question_display(
        attempt_id=attempt_id,
        test_id=test_id,
        order_no=order_no,
        started_at=datetime.now(timezone.utc),
        time_limit_min=time_limit,
    )

    feedback = "✅ Javob saqlandi: " + ", ".join(saved_info)
    await message.answer(feedback, reply_markup=get_main_menu_keyboard())
    await message.answer(text, reply_markup=kb)
