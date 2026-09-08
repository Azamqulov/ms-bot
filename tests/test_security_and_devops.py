"""
Kiberxavfsizlik (Audit 3), DevOps va Backend arxitekturasi (Audit 1, 4) uchun yangi testlar to'plami.
"""

import time
import pytest
from httpx import AsyncClient, ASGITransport
from bot.web_app.api import app
from bot.database.session import init_db
from bot.database.seed_data import seed_database
from bot.core.rate_limiter import SlidingWindowRateLimiter
from bot.core.security import create_student_session_token, verify_student_session_token


@pytest.mark.asyncio
async def test_healthz_endpoint():
    """DevOps healthcheck /healthz endpointining to'g'ri ishlashi"""
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/healthz")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["service"] == "MSBot API"
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_student_session_token_flow():
    """Talaba sessiya tokeni generatsiyasi va HMAC anti-spoofing tekshiruvi"""
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Yangi sessiya tokeni olish
        session_res = await client.post(
            "/api/test/session",
            json={"telegram_id": 12345678, "test_id": 1}
        )
        assert session_res.status_code == 200
        data = session_res.json()
        assert "session_token" in data
        token = data["session_token"]

        # 2. Tokenni tekshirish
        is_valid, payload, err = verify_student_session_token(token)
        assert is_valid is True
        assert payload["tg_id"] == 12345678
        assert payload["test_id"] == 1
        assert err is None

        # 3. Buzilgan (tampered) token tekshiruvi
        fake_token = token[:-5] + "XXXXX"
        is_fake_valid, _, fake_err = verify_student_session_token(fake_token)
        assert is_fake_valid is False
        assert "noto'g'ri" in fake_err.lower()

        # 4. Muddat tugagan token tekshiruvi
        expired_token = create_student_session_token(
            telegram_id=12345678,
            test_id=1,
            expires_in_seconds=-10
        )
        is_exp_valid, _, exp_err = verify_student_session_token(expired_token)
        assert is_exp_valid is False
        assert "tugagan" in exp_err.lower()


@pytest.mark.asyncio
async def test_rate_limiter_logic():
    """Sliding Window Rate Limiter 429 xatosi qaytarishini tekshirish"""
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=5)
    client_ip = "192.168.1.100"

    # Birinchi 3 ta so'rov ruxsat berilishi kerak
    allowed_1, _ = await limiter.is_allowed(client_ip)
    allowed_2, _ = await limiter.is_allowed(client_ip)
    allowed_3, _ = await limiter.is_allowed(client_ip)
    assert allowed_1 is True
    assert allowed_2 is True
    assert allowed_3 is True

    # 4-chi so'rov bloklanishi kerak (Rate limit oshdi)
    allowed_4, retry_after = await limiter.is_allowed(client_ip)
    assert allowed_4 is False
    assert retry_after > 0


@pytest.mark.asyncio
async def test_submit_with_mismatched_session_token():
    """Sessiya tokeni boshqa foydalanuvchiga tegishli bo'lsa 403 xatosi berishi"""
    await init_db()
    token = create_student_session_token(telegram_id=11111, test_id=1)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/test/submit",
            headers={"X-Session-Token": token},
            json={
                "test_id": 1,
                "telegram_id": 99999,  # Token 11111 ga tegishli, lekin 99999 yuborilmoqda
                "full_name": "Spoofer User",
                "answers": [],
            }
        )
        assert res.status_code == 403
        assert "mos emas" in res.json()["detail"].lower()
