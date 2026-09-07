from typing import Optional, Dict, List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_question_keyboard(
    question_type: str,
    order_no: int,
    total_questions: int = 45,
    user_answer: Optional[str] = None,
    subpart_answers: Optional[Dict[str, str]] = None,
) -> InlineKeyboardMarkup:
    """
    Savol turiga qarab mos inline klaviatura yaratish:
    - Y-1: A, B, C, D variantlar
    - GROUPED: A, B, C, D, E, F variantlar
    - O: a) va b) bandlariga javob kiritish tugmalari
    """
    builder = InlineKeyboardBuilder()

    # 1. Variantlar qatori
    if question_type == "Y-1":
        options = ["A", "B", "C", "D"]
        row = []
        for opt in options:
            label = f"✅ {opt}" if user_answer == opt else opt
            row.append(
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"ans:{order_no}:{opt}"
                )
            )
        builder.row(*row)

    elif question_type == "GROUPED":
        options = ["A", "B", "C", "D", "E", "F"]
        # 3 tadan 2 qator
        row1 = []
        for opt in options[:3]:
            label = f"✅ {opt}" if user_answer == opt else opt
            row1.append(
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"ans:{order_no}:{opt}"
                )
            )
        row2 = []
        for opt in options[3:]:
            label = f"✅ {opt}" if user_answer == opt else opt
            row2.append(
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"ans:{order_no}:{opt}"
                )
            )
        builder.row(*row1)
        builder.row(*row2)

    elif question_type == "O":
        # a va b bandlari uchun javob kiritish tugmalari
        ans_a = (subpart_answers or {}).get("a")
        ans_b = (subpart_answers or {}).get("b")

        btn_a_text = f"✍️ a) bandiga javob: {ans_a}" if ans_a else "✍️ a) bandiga javob kiritish"
        btn_b_text = f"✍️ b) bandiga javob: {ans_b}" if ans_b else "✍️ b) bandiga javob kiritish"

        builder.row(InlineKeyboardButton(text=btn_a_text, callback_data=f"open_input:{order_no}:a"))
        builder.row(InlineKeyboardButton(text=btn_b_text, callback_data=f"open_input:{order_no}:b"))

    # 2. Navigatsiya qatori: Oldingi / Keyingi
    nav_row = []
    if order_no > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"nav:{order_no - 1}"))
    if order_no < total_questions:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"nav:{order_no + 1}"))
    if nav_row:
        builder.row(*nav_row)

    # 3. Amallar qatori: Savollar ro'yxati va Yakunlash
    action_row = [
        InlineKeyboardButton(text="📋 Barcha savollar", callback_data=f"grid:{order_no}"),
        InlineKeyboardButton(text="🏁 Testni yakunlash", callback_data="confirm_finish"),
    ]
    builder.row(*action_row)

    return builder.as_markup()


def get_questions_grid_keyboard(
    current_order: int,
    total_questions: int,
    answered_orders: set[int]
) -> InlineKeyboardMarkup:
    """
    45 ta savolni tezkor tanlash uchun kataklar klaviaturasi (Grid)
    """
    builder = InlineKeyboardBuilder()

    # Har qatorda 5 ta tugma
    row: List[InlineKeyboardButton] = []
    for i in range(1, total_questions + 1):
        if i == current_order:
            text = f"📍{i}"
        elif i in answered_orders:
            text = f"✅{i}"
        else:
            text = f"{i}"

        row.append(InlineKeyboardButton(text=text, callback_data=f"nav:{i}"))
        if len(row) == 5:
            builder.row(*row)
            row = []

    if row:
        builder.row(*row)

    # Orqaga qaytish va Yakunlash
    builder.row(
        InlineKeyboardButton(text="🔙 Joriy savolga qaytish", callback_data=f"nav:{current_order}"),
        InlineKeyboardButton(text="🏁 Testni yakunlash", callback_data="confirm_finish"),
    )

    return builder.as_markup()


def get_finish_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Testni yakunlashni tasdiqlash klaviaturasi"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Ha, testni yakunlash", callback_data="do_finish"),
        InlineKeyboardButton(text="❌ Davom ettirish", callback_data="cancel_finish"),
    )
    return builder.as_markup()


def get_restart_keyboard() -> InlineKeyboardMarkup:
    """Natijadan keyin qayta topshirish tugmasi"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Yangi test boshlash", callback_data="start_test_prompt"),
        InlineKeyboardButton(text="📊 Natijalarim", callback_data="show_my_history"),
    )
    return builder.as_markup()
