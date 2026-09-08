import time
import pytest
from httpx import AsyncClient, ASGITransport
from bot.web_app.api import app
from bot.database.session import init_db
from bot.database.seed_data import seed_database
from bot.database.models import Test
from sqlalchemy import select
from bot.database.session import async_session_maker


@pytest.mark.asyncio
async def test_submission_speed_under_one_second():
    """45 talik test topshirish tezligi 1 soniyadan kam bo'lishini tekshirish (Benchmark)"""
    await init_db()
    await seed_database()

    async with async_session_maker() as session:
        t_stmt = select(Test).where(Test.is_active == True)
        res = await session.execute(t_stmt)
        test_obj = res.scalars().first()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        get_res = await client.get(f"/api/test/{test_obj.code}")
        assert get_res.status_code == 200
        questions = get_res.json()["questions"]

        # 45 ta savol uchun javoblar tayyorlash
        answers_payload = []
        for q in questions:
            answers_payload.append({
                "question_id": q["id"],
                "user_answer": "B",
                "sub_part_label": None,
            })

        start_time = time.perf_counter()
        submit_res = await client.post(
            "/api/test/submit",
            json={
                "test_id": test_obj.id,
                "telegram_id": 777888999,
                "full_name": "Tezkor Talaba",
                "username": "fast_student",
                "answers": answers_payload,
            }
        )
        duration = time.perf_counter() - start_time
        assert submit_res.status_code == 200
        data = submit_res.json()
        assert data["success"] is True
        assert "final_score" in data
        assert "grade" in data

        print(f"\n[BENCHMARK] 45 ta savolli testni hisoblash vaqti: {duration:.3f} soniya!")
        assert duration < 1.0, f"Hisoblash 1 soniyadan oshib ketdi: {duration:.3f}s"
