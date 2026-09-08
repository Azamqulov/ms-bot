import pytest
from bot.database.session import init_db
from bot.database.models import Test, Question, User, Attempt
from bot.services.attempt_service import process_test_submission
from bot.services.admin_service import get_attempt_detailed_answers
from bot.database.session import async_session_maker


@pytest.mark.asyncio
async def test_open_and_closed_evaluation_robustness():
    await init_db()

    import uuid
    from bot.services.test_service import get_or_create_user

    user = await get_or_create_user(
        telegram_id=888777666,
        full_name="Eshmat Toshmatov",
        username="eshmat",
    )

    test_code = f"EVAL-{uuid.uuid4().hex[:6].upper()}"
    async with async_session_maker() as session:
        # Create test with closed and open questions
        test = Test(
            code=test_code,
            title="Baholash Testi",
            created_by_user_id=user.id,
            is_active=True,
        )
        session.add(test)
        await session.flush()

        # 1. Closed question (Y-1)
        q1 = Question(
            test_id=test.id,
            order_no=1,
            type="Y-1",
            text="Yopiq savol 1",
            options={"A": "10", "B": "20", "C": "30", "D": "40"},
            correct_answer="B",
            difficulty_b=0.0,
        )
        session.add(q1)

        # 2. Open question with type "O-1" and alternative answers
        q36 = Question(
            test_id=test.id,
            order_no=36,
            type="O-1",
            text="Yozma ochiq savol 36",
            sub_parts=[
                {
                    "label": "a",
                    "correct_answer": "12",
                    "alternative_answers": ["12.0", "12,0"],
                },
                {
                    "label": "b",
                    "correct_answer": "3/4",
                    "alternative_answers": ["0.75", "0,75"],
                },
            ],
            difficulty_b=0.5,
        )
        session.add(q36)

        # 3. Open question with type "O"
        q37 = Question(
            test_id=test.id,
            order_no=37,
            type="O",
            text="Yozma ochiq savol 37",
            sub_parts=[
                {
                    "label": "a",
                    "correct_answer": "100",
                    "alternative_answers": [],
                },
                {
                    "label": "b",
                    "correct_answer": "50; 50.0",
                    "alternative_answers": [],
                },
            ],
            difficulty_b=0.8,
        )
        session.add(q37)

        await session.commit()
        test_id = test.id
        q1_id = q1.id
        q36_id = q36.id
        q37_id = q37.id
        u_tg_id = user.telegram_id

    # Answers to submit:
    # q1: " b " (lowercase with spaces -> should match "B")
    # q36 a: " 12,0 " (alternative answer)
    # q36 b: "0.75" (alternative answer)
    # q37 a: "100" (exact match)
    # q37 b: "99" (wrong)
    answers_payload = [
        {"question_id": q1_id, "user_answer": "  b  ", "sub_part_label": None},
        {"question_id": q36_id, "user_answer": " 12,0 ", "sub_part_label": "a"},
        {"question_id": q36_id, "user_answer": "0.75", "sub_part_label": "b"},
        {"question_id": q37_id, "user_answer": "100", "sub_part_label": "a"},
        {"question_id": q37_id, "user_answer": "99", "sub_part_label": "b"},
    ]

    result = await process_test_submission(
        test_id=test_id,
        telegram_id=u_tg_id,
        full_name="Eshmat Toshmatov",
        username="eshmat",
        answers=answers_payload,
    )

    assert result["success"] is True
    # Correct: q1 (+1), q36a (+1), q36b (+1), q37a (+1) -> Total 4 out of 5 items
    assert result["raw_score"] == 4
    attempt_id = result["attempt_id"]

    # Now verify admin breakdown view
    breakdown_data = await get_attempt_detailed_answers(attempt_id, admin_user_id=user.id)
    assert breakdown_data is not None
    assert len(breakdown_data["breakdown"]) == 3

    # Check q1 in breakdown
    bd_q1 = next(q for q in breakdown_data["breakdown"] if q["question_id"] == q1_id)
    assert bd_q1["is_correct"] is True
    assert bd_q1["status"] == "correct"

    # Check q36 in breakdown
    bd_q36 = next(q for q in breakdown_data["breakdown"] if q["question_id"] == q36_id)
    assert bd_q36["type"] == "O"
    assert bd_q36["is_correct"] is True
    assert len(bd_q36["sub_parts"]) == 2
    assert bd_q36["sub_parts"][0]["is_correct"] is True
    assert bd_q36["sub_parts"][1]["is_correct"] is True

    # Check q37 in breakdown
    bd_q37 = next(q for q in breakdown_data["breakdown"] if q["question_id"] == q37_id)
    assert bd_q37["type"] == "O"
    assert bd_q37["is_correct"] is False
    assert bd_q37["status"] == "partially_correct"
    assert bd_q37["sub_parts"][0]["is_correct"] is True
    assert bd_q37["sub_parts"][1]["is_correct"] is False
