import io
import pytest
from httpx import AsyncClient, ASGITransport
from bot.web_app.api import app
from bot.database.session import init_db
from bot.database.seed_data import seed_database


@pytest.mark.asyncio
async def test_web_api_endpoints():
    await init_db()
    await seed_database()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. STANDART test ma'lumotlarini olish
        res = await client.get("/api/test/STANDART")
        assert res.status_code == 200
        data = res.json()
        assert data["code"] == "STANDART"
        assert len(data["questions"]) == 45

        # 2. Rasm yuklash testi
        fake_file = io.BytesIO(b"fake image data")
        files = {"file": ("geometry.png", fake_file, "image/png")}
        img_res = await client.post("/api/admin/upload-image", files=files)
        assert img_res.status_code == 200
        img_data = img_res.json()
        assert "url" in img_data
        assert img_data["url"].startswith("/uploads/")

        # 3. Admin orqali yangi test yaratish
        import uuid
        unique_code = f"WEB-{uuid.uuid4().hex[:4].upper()}"
        new_test_payload = {
            "creator_telegram_id": 1685356708,
            "code": unique_code,
            "title": "Veb Geometriya Testi",
            "description": "Geometrik masalalar",
            "time_limit_min": 120,
            "questions": [
                {
                    "order_no": 1,
                    "type": "Y-1",
                    "section": "Geometriya",
                    "difficulty_b": 0.5,
                    "text": "Parallelogramm yuzi $72\\text{ cm}^2$.",
                    "image_url": img_data["url"],
                    "options": {"A": "24", "B": "36", "C": "48", "D": "12"},
                    "correct_answer": "B"
                }
            ]
        }
        create_res = await client.post("/api/admin/create-test", json=new_test_payload)
        assert create_res.status_code == 200
        created_data = create_res.json()
        assert created_data["code"] == unique_code

        # 4. Yaratilgan testni qayta o'qish
        get_res = await client.get(f"/api/test/{unique_code}")
        assert get_res.status_code == 200
        assert get_res.json()["questions"][0]["image_url"] == img_data["url"]

        # 5. Test javoblarini topshirish (Submit)
        submit_payload = {
            "test_id": created_data["test_id"],
            "telegram_id": 1685356708,
            "full_name": "Web Test User",
            "username": "web_user",
            "answers": [
                {
                    "question_id": get_res.json()["questions"][0]["id"],
                    "user_answer": "B",
                    "sub_part_label": None
                }
            ]
        }
        submit_res = await client.post("/api/test/submit", json=submit_payload)
        assert submit_res.status_code == 200
        sub_data = submit_res.json()
        assert sub_data["raw_score"] == 1
        assert "final_score" in sub_data
        assert "grade" in sub_data

        # 6. User profile endpointi testi
        user_res = await client.get("/api/user/1685356708")
        assert user_res.status_code == 200
        user_data = user_res.json()
        assert "registered" in user_data
        assert "full_name" in user_data
