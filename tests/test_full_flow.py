import pytest
from bot.database.session import init_db
from bot.database.seed_data import seed_database
from bot.services.test_service import (
    get_or_create_user,
    get_default_test,
    start_new_attempt,
    get_question_by_order,
    save_answer,
    finish_attempt,
    get_user_attempts_history,
)
from bot.services.report_service import generate_result_report, generate_history_report
from bot.core.validator import check_open_answer


@pytest.mark.asyncio
async def test_complete_user_test_flow():
    # 1. Bazani initsializatsiya qilish va seed
    await init_db()
    test_obj = await seed_database()
    assert test_obj is not None

    # 2. Foydalanuvchini yaratish
    user = await get_or_create_user(
        telegram_id=999888777,
        full_name="Alisher Navoiy",
        username="alisher_math",
    )
    assert user.id is not None

    # 3. Yangi attempt boshlash
    attempt = await start_new_attempt(user_id=user.id, test_id=test_obj.id)
    assert attempt.status == "in_progress"

    # 4. Savollarga javob berish
    # 1-32 Y-1 savollar:
    for order_no in range(1, 33):
        q = await get_question_by_order(test_obj.id, order_no)
        assert q is not None
        # Deyarli barcha savollarga to'g'ri javob beramiz (yaxshi ball uchun)
        ans = q.correct_answer
        is_corr = (ans == q.correct_answer)
        await save_answer(
            attempt_id=attempt.id,
            question_id=q.id,
            user_answer=ans,
            is_correct=is_corr,
        )

    # 33-35 Guruhlangan savollar:
    for order_no in range(33, 36):
        q = await get_question_by_order(test_obj.id, order_no)
        assert q is not None
        ans = q.correct_answer
        await save_answer(
            attempt_id=attempt.id,
            question_id=q.id,
            user_answer=ans,
            is_correct=True,
        )

    # 36-45 Ochiq savollar (a va b bandlari):
    for order_no in range(36, 46):
        q = await get_question_by_order(test_obj.id, order_no)
        assert q is not None
        for sp in q.sub_parts:
            label = sp["label"]
            correct_val = sp["correct_answer"].split(";")[0].strip()
            await save_answer(
                attempt_id=attempt.id,
                question_id=q.id,
                user_answer=correct_val,
                is_correct=True,
                sub_part_label=label,
            )

    # 5. Testni yakunlash (RASH modeli hisobi)
    completed_attempt, rasch_result = await finish_attempt(attempt.id)

    assert completed_attempt.status == "completed"
    assert completed_attempt.raw_score == 55  # Barchasi to'g'ri
    assert completed_attempt.final_score is not None
    assert completed_attempt.final_score >= 70.0  # A+ darajasi
    assert completed_attempt.grade == "A+"
    assert completed_attempt.is_certified is True

    # 6. Hisobot generatsiyasini tekshirish
    report_text = generate_result_report(user, completed_attempt, rasch_result)
    assert "MILLIY SERTIFIKAT" in report_text
    assert "A+" in report_text
    assert f"{completed_attempt.final_score:.1f}" in report_text

    # 7. Natijalar tarixi tekshiruvi
    history = await get_user_attempts_history(user.id)
    assert len(history) >= 1
    history_report = generate_history_report(history)
    assert "SIZNING NATIJALARINGIZ TARIXI" in history_report
