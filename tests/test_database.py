import pytest
from sqlalchemy import select
from bot.database.session import init_db, async_session_maker
from bot.database.models import Test, Question, QuestionGroup
from bot.database.seed_data import seed_database


@pytest.mark.asyncio
async def test_init_db_and_seeding():
    await init_db()
    test_obj = await seed_database()

    assert test_obj is not None
    assert test_obj.question_count == 45

    async with async_session_maker() as session:
        # 45 ta savol borligini tekshirish
        stmt = select(Question).where(Question.test_id == test_obj.id).order_by(Question.order_no)
        res = await session.execute(stmt)
        questions = res.scalars().all()

        assert len(questions) == 45

        # 1-32 Y-1 ekanligini tekshirish
        for q in questions[:32]:
            assert q.type == "Y-1"
            assert q.options is not None
            assert len(q.options) == 4

        # 33-35 guruhlangan ekanligini tekshirish
        for q in questions[32:35]:
            assert q.type == "GROUPED"
            assert q.group_id is not None

        # 36-45 ochiq ekanligini tekshirish
        for q in questions[35:]:
            assert q.type == "O"
            assert q.sub_parts is not None
            assert len(q.sub_parts) == 2
