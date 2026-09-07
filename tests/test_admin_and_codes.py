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

