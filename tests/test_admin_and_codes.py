import pytest
from bot.database.session import init_db
from bot.services.test_service import get_or_create_user
from bot.services.admin_service import (
    is_super_admin,
    is_admin,
    add_admin,
    remove_admin,
    create_test_with_questions,
    get_test_by_code,
    get_admin_tests,
)
from bot.config import settings


@pytest.mark.asyncio
async def test_super_admin_and_admin_management():
    await init_db()

    # 1. Super admin tekshiruvi (1685356708)
    assert is_super_admin(1685356708) is True
    assert await is_admin(1685356708) is True
    assert is_super_admin(999999999) is False

    # 2. Yangi admin qo'shish
    target_id = 777123456
    success, msg = await add_admin(target_id)
    assert success is True
    assert await is_admin(target_id) is True

    # 3. Super adminni o'chirishga yo'l qo'yilmasligi
    s_del, s_msg = await remove_admin(settings.SUPER_ADMIN_ID)
    assert s_del is False

    # 4. Adminni o'chirish
    del_ok, del_msg = await remove_admin(target_id)
    assert del_ok is True
    assert await is_admin(target_id) is False


@pytest.mark.asyncio
async def test_create_and_access_test_by_code():
    await init_db()

    admin_user = await get_or_create_user(1685356708, "Super Admin")

    sample_questions = [
        {
            "order_no": 1,
            "type": "Y-1",
            "section": "Algebra",
            "difficulty_b": -0.5,
            "text": "Hisoblang: 10 + 15",
            "options": {"A": "25", "B": "20", "C": "30", "D": "15"},
            "correct_answer": "A",
        },
        {
            "order_no": 2,
            "type": "O",
            "section": "Geometriya",
            "difficulty_b": 0.8,
            "text": "Kvadrat tomoni 5 ga teng.\na) Perimetrini toping.\nb) Yuzini toping.",
            "sub_parts": [
                {"label": "a", "correct_answer": "20", "difficulty_b": 0.5},
                {"label": "b", "correct_answer": "25", "difficulty_b": 1.0},
            ],
        },
    ]

    # Test yuklash
    import uuid
    test_code = f"TEST-MATH-{uuid.uuid4().hex[:6].upper()}"
    success, msg, test_obj = await create_test_with_questions(
        creator_user_id=admin_user.id,
        code=test_code,
        title="7-sinf Matematika Olimpiada",
        description="Namunaviy olimpiada testi",
        time_limit_min=60,
        questions_data=sample_questions,
    )

    assert success is True
    assert test_obj is not None
    assert test_obj.code == test_code
    assert test_obj.question_count == 2

    # Takroriy kod bilan yuklashga ruxsat bermaslik
    dup_ok, dup_msg, _ = await create_test_with_questions(
        creator_user_id=admin_user.id,
        code=test_code,
        title="Boshqa test",
        description="",
        time_limit_min=60,
        questions_data=sample_questions,
    )
    assert dup_ok is False

    # Kod orqali testni olish
    retrieved = await get_test_by_code(test_code)
    assert retrieved is not None
    assert retrieved.title == "7-sinf Matematika Olimpiada"
    assert len(retrieved.questions) == 2

    # Mavjud bo'lmagan kod
    assert await get_test_by_code("NON_EXISTENT_CODE") is None

    # Admin testlar ro'yxatini tekshirish
    my_tests = await get_admin_tests(admin_user.id)
    codes = [t["code"] for t in my_tests]
    assert test_code in codes


@pytest.mark.asyncio
async def test_admin_api_authentication_security():
    """
    Admin API endpointlari autentifikatsiya va avtorizatsiyasini to'liq tekshirish:
    - Headersiz so'rov -> 401
    - Noto'g'ri hash (soxta ma'lumot) -> 401
    - Eskirgan sessiya (auth_date > 24 soat) -> 401
    - Oddiy (admin bo'lmagan) user -> 403
    - Haqiqiy admin initData -> 200
    """
    import time
    import uuid
    from httpx import AsyncClient, ASGITransport
    from bot.web_app.api import app
    from bot.web_app.auth import create_mock_init_data

    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        test_payload = {
            "code": f"AUTH-{uuid.uuid4().hex[:6].upper()}",
            "title": "Xavfsizlik Testi",
            "time_limit_min": 60,
            "questions": [
                {
                    "order_no": 1,
                    "type": "Y-1",
                    "text": "Savol",
                    "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
                    "correct_answer": "A",
                }
            ],
        }

        # 1. Sarlavhasiz (hech qanday X-Telegram-Init-Data siz)
        res_no_header = await client.post("/api/admin/create-test", json=test_payload)
        assert res_no_header.status_code == 401
        assert "talab qilinadi" in res_no_header.json().get("detail", "")

        # 2. Noto'g'ri / soxta hash bilan
        fake_init_data = create_mock_init_data(
            user_id=settings.SUPER_ADMIN_ID,
            bot_token=settings.BOT_TOKEN,
            is_valid=False,
        )
        res_fake_hash = await client.post(
            "/api/admin/create-test",
            json=test_payload,
            headers={"X-Telegram-Init-Data": fake_init_data},
        )
        assert res_fake_hash.status_code == 401
        assert "hash mos kelmadi" in res_fake_hash.json().get("detail", "")

        # 3. Eskirgan auth_date (> 24 soat oldin)
        expired_time = int(time.time()) - 100000
        expired_init_data = create_mock_init_data(
            user_id=settings.SUPER_ADMIN_ID,
            bot_token=settings.BOT_TOKEN,
            auth_date=expired_time,
            is_valid=True,
        )
        res_expired = await client.post(
            "/api/admin/create-test",
            json=test_payload,
            headers={"X-Telegram-Init-Data": expired_init_data},
        )
        assert res_expired.status_code == 401
        assert "eskirgan" in res_expired.json().get("detail", "")

        # 4. Admin bo'lmagan oddiy begona foydalanuvchi (403 Forbidden)
        non_admin_id = 999111222
        non_admin_init_data = create_mock_init_data(
            user_id=non_admin_id,
            bot_token=settings.BOT_TOKEN,
            is_valid=True,
        )
        res_forbidden = await client.post(
            "/api/admin/create-test",
            json=test_payload,
            headers={"X-Telegram-Init-Data": non_admin_init_data},
        )
        assert res_forbidden.status_code == 403
        assert "admin" in res_forbidden.json().get("detail", "").lower()

        # 5. Haqiqiy Super Admin initData bilan (200 OK)
        valid_admin_init_data = create_mock_init_data(
            user_id=settings.SUPER_ADMIN_ID,
            bot_token=settings.BOT_TOKEN,
            is_valid=True,
        )
        res_ok = await client.post(
            "/api/admin/create-test",
            json=test_payload,
            headers={"X-Telegram-Init-Data": valid_admin_init_data},
        )
        assert res_ok.status_code == 200
        assert res_ok.json()["success"] is True

        created_test_id = res_ok.json()["test_id"]

        # 6. Admin test ma'lumotlari va kalitlarini olish (GET /api/admin/test-details/{test_id})
        res_details = await client.get(
            f"/api/admin/test-details/{created_test_id}",
            headers={"X-Telegram-Init-Data": valid_admin_init_data},
        )
        assert res_details.status_code == 200
        details_data = res_details.json()["test"]
        assert details_data["id"] == created_test_id
        assert len(details_data["questions"]) == 1
        assert details_data["questions"][0]["correct_answer"] == "A"

        # 7. Kalitlarni tahrirlash va saqlash (POST /api/admin/tests/{test_id}/update)
        res_update = await client.post(
            f"/api/admin/tests/{created_test_id}/update",
            json={
                "title": "Yangilangan Xavfsizlik Testi",
                "time_limit_min": 90,
                "questions": [
                    {
                        "order_no": 1,
                        "correct_answer": "C",
                    }
                ]
            },
            headers={"X-Telegram-Init-Data": valid_admin_init_data},
        )
        assert res_update.status_code == 200
        assert res_update.json()["success"] is True

        # 8. Qayta tekshirish: kalit "C" ga o'zgarganini tasdiqlash
        res_details_after = await client.get(
            f"/api/admin/test-details/{created_test_id}",
            headers={"X-Telegram-Init-Data": valid_admin_init_data},
        )
        assert res_details_after.status_code == 200
        after_data = res_details_after.json()["test"]
        assert after_data["title"] == "Yangilangan Xavfsizlik Testi"
        assert after_data["time_limit_min"] == 90
        assert after_data["questions"][0]["correct_answer"] == "C"

        # 9. Test statistikasi va natijalari (GET /api/admin/tests/{test_id}/stats)
        res_stats = await client.get(
            f"/api/admin/tests/{created_test_id}/stats",
            headers={"X-Telegram-Init-Data": valid_admin_init_data},
        )
        assert res_stats.status_code == 200
        stats_data = res_stats.json()
        assert stats_data["test_id"] == created_test_id
        assert "total_participants" in stats_data
        assert "avg_score" in stats_data
        assert "participants" in stats_data

        # 10. Test statistikasini Telegramga post qilib yuborish (POST /api/admin/tests/{test_id}/send-telegram-post)
        res_post = await client.post(
            f"/api/admin/tests/{created_test_id}/send-telegram-post",
            json={"target_chat": "1685356708"},
            headers={"X-Telegram-Init-Data": valid_admin_init_data},
        )
        assert res_post.status_code == 200
        post_data = res_post.json()
        assert post_data["success"] is True
        assert "post_text" in post_data
        assert "TEST NATIJALARI VA STATISTIKASI" in post_data["post_text"]
        assert "TALABGORLAR VA NATIJALAR" in post_data["post_text"]


@pytest.mark.asyncio
async def test_hide_answers_submission_flow():
    """hide_answers=True bo'lganda talabgorga natijalar yashirilishi va 'Natijalarni ustozingiz chiqaradi' qaytarilishini tekshirish"""
    from httpx import AsyncClient, ASGITransport
    from bot.web_app.api import app

    await init_db()
    admin_user = await get_or_create_user(1685356708, "Super Admin")

    sample_questions = [
        {
            "order_no": 1,
            "type": "Y-1",
            "section": "Algebra",
            "difficulty_b": 0.0,
            "text": "1-savol",
            "options": {"A": "A", "B": "B", "C": "C", "D": "D"},
            "correct_answer": "B",
        }
    ]

    import uuid
    test_code = f"TEST_HIDE_{uuid.uuid4().hex[:6].upper()}"

    success, msg, test_obj = await create_test_with_questions(
        creator_user_id=admin_user.id,
        code=test_code,
        title="Yashirin Natijali Test",
        description="",
        time_limit_min=120,
        questions_data=sample_questions,
        hide_answers=True,
    )
    assert success is True, f"Create test failed: {msg}"
    assert test_obj.hide_answers is True

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. API dan testni olishda hide_answers=True ekanligi
        res_get = await client.get(f"/api/test/{test_code}")
        assert res_get.status_code == 200
        get_data = res_get.json()
        assert get_data["hide_answers"] is True
        q_id = get_data["questions"][0]["id"]

        # 2. Testni topshirganda faqat xabar qaytishi (natija va ballar yashiriladi)
        res_sub = await client.post(
            "/api/test/submit",
            json={
                "test_id": test_obj.id,
                "telegram_id": 999111222,
                "full_name": "O'quvchi Test",
                "answers": [
                    {
                        "question_id": q_id,
                        "user_answer": "B",
                        "sub_part_label": None,
                    }
                ]
            }
        )
        assert res_sub.status_code == 200
        sub_data = res_sub.json()
        assert sub_data["hide_answers"] is True
        assert "ustozingiz" in sub_data["message"].lower()
        # raw_score va cert_url talabgorga qaytarilmasligi
        assert "raw_score" not in sub_data
        assert "certificate_url" not in sub_data


def test_format_telegram_stats_post():
    """Foydalanuvchi talabi bo'yicha Telegram post formatini tekshirish:
    Ism Familiya ------ nechta to'g'ri topgani, to'plagan bali va darajasi (✅ berildi / ❌ berilmadi)"""
    from bot.services.report_service import format_telegram_stats_post

    dummy_stats = {
        "test_id": 1,
        "test_code": "111",
        "test_title": "Milliy Sertifikat Matematika (1-variant)",
        "question_count": 45,
        "time_limit_min": 150,
        "total_participants": 2,
        "completed_count": 2,
        "certified_count": 1,
        "avg_score": 53.5,
        "highest_score": 75.0,
        "participants": [
            {
                "rank": 1,
                "full_name": "Admin",
                "raw_score": 35,
                "final_score": 75.0,
                "grade": "A+",
                "is_certified": True,
            },
            {
                "rank": 2,
                "full_name": "Valiyev Ali",
                "raw_score": 20,
                "final_score": 32.0,
                "grade": "Sertifikat berilmaydi",
                "is_certified": False,
            }
        ]
    }

    messages = format_telegram_stats_post(dummy_stats)
    assert len(messages) >= 1
    post = messages[0]
    assert "TEST NATIJALARI VA STATISTIKASI" in post
    assert "#111" in post
    # Talab qilingan format tekshiruvi:
    assert "Admin</b> ------ 🎯 35 ta to'g'ri, ⭐️ 75.0 ball, A+ (✅ Sertifikat berildi)" in post
    assert "Valiyev Ali</b> ------ 🎯 20 ta to'g'ri, ⭐️ 32.0 ball, ❌ Sertifikat berilmadi" in post


@pytest.mark.asyncio
async def test_duplicate_test_code_prevention():
    """Bir xil kodli test yaratishga yo'l qo'ymaslikni tekshirish"""
    import time
    from bot.services.admin_service import create_test_with_questions

    admin_user = await get_or_create_user(settings.SUPER_ADMIN_ID, "Super Admin")
    unique_code = f"DUP-{int(time.time())}"

    # 1. Birinchi marta yaratish muvaffaqiyatli
    ok, msg, test1 = await create_test_with_questions(
        creator_user_id=admin_user.id,
        code=unique_code,
        title="Original Test",
        description="Original desc",
        time_limit_min=150,
        questions_data=[
            {"order_no": 1, "type": "Y-1", "correct_answer": "A"}
        ]
    )
    assert ok is True
    assert test1.code == unique_code

    # 2. Xuddi shu kod (yoki kichik harflar bilan) qayta yaratish rad etilishi shart
    ok2, msg2, test2 = await create_test_with_questions(
        creator_user_id=admin_user.id,
        code=unique_code.lower(),
        title="Duplicate Test",
        description="Duplicate desc",
        time_limit_min=150,
        questions_data=[
            {"order_no": 1, "type": "Y-1", "correct_answer": "B"}
        ]
    )
    assert ok2 is False
    assert test2 is None
    assert "allaqachon mavjud" in msg2


@pytest.mark.asyncio
async def test_attempt_detailed_answers_breakdown():
    """O'quvchining har bir savol bo'yicha javoblari va to'g'ri javoblari tahlilini tekshirish"""
    import time
    from bot.services.admin_service import create_test_with_questions, get_attempt_detailed_answers
    from bot.database.models import User, Attempt, AttemptAnswer, Question
    from bot.database.session import async_session_maker

    admin_user = await get_or_create_user(settings.SUPER_ADMIN_ID, "Super Admin")
    test_code = f"BRK-{int(time.time())}"
    ok, msg, created_test = await create_test_with_questions(
        creator_user_id=admin_user.id,
        code=test_code,
        title="Breakdown Test",
        description="Breakdown desc",
        time_limit_min=150,
        questions_data=[
            {"order_no": 1, "type": "Y-1", "correct_answer": "A"},
            {"order_no": 2, "type": "Y-1", "correct_answer": "B"},
            {"order_no": 36, "type": "O", "sub_parts": [{"label": "a", "correct_answer": "12"}]}
        ]
    )
    assert ok is True

    u = await get_or_create_user(telegram_id=98765400 + int(time.time() % 100000), full_name="Sinovchi O'quvchi")

    async with async_session_maker() as session:
        # Urinish yaratish

        att = Attempt(
            test_id=created_test.id,
            user_id=u.id,
            raw_score=1,
            final_score=15.0,
            grade="C",
            is_certified=False,
            status="completed"
        )
        session.add(att)
        await session.flush()

        # 1-savol to'g'ri ('A'), 2-savol xato ('C'), 36-savol javob berilmagan
        from sqlalchemy import select
        q1 = (await session.execute(select(Question).where(Question.test_id == created_test.id, Question.order_no == 1))).scalar_one()
        q2 = (await session.execute(select(Question).where(Question.test_id == created_test.id, Question.order_no == 2))).scalar_one()

        ans1 = AttemptAnswer(attempt_id=att.id, question_id=q1.id, user_answer="A", is_correct=True)
        ans2 = AttemptAnswer(attempt_id=att.id, question_id=q2.id, user_answer="C", is_correct=False)
        session.add_all([ans1, ans2])
        await session.commit()
        att_id = att.id
        admin_uid = (await session.execute(select(User).where(User.telegram_id == settings.SUPER_ADMIN_ID))).scalar_one().id

    # Detalizatsiyani chaqirib tekshirish
    breakdown_data = await get_attempt_detailed_answers(attempt_id=att_id, admin_user_id=admin_uid)
    assert breakdown_data is not None
    assert breakdown_data["full_name"] == "Sinovchi O'quvchi"
    assert breakdown_data["correct_count"] == 1
    assert breakdown_data["wrong_count"] == 1
    assert breakdown_data["unanswered_count"] == 1

    items = breakdown_data["breakdown"]
    assert len(items) == 3
    # 1-savol: to'g'ri
    assert items[0]["order_no"] == 1
    assert items[0]["user_answer"] == "A"
    assert items[0]["status"] == "correct"
    # 2-savol: noto'g'ri
    assert items[1]["order_no"] == 2
    assert items[1]["user_answer"] == "C"
    assert items[1]["correct_answer"] == "B"
    assert items[1]["status"] == "wrong"
    # 36-savol: yechilmagan
    assert items[2]["order_no"] == 36
    assert items[2]["status"] == "unanswered"




