"""
FastAPI Web App va REST API moduli:
Telegram Mini App (TMA) va Admin Web Konstruktori uchun.
"""

import os
import shutil
import uuid
import logging
import time
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.config import settings
from bot.database.session import async_session_maker
from bot.database.models import Test, Question, QuestionGroup, User, AttemptAnswer
from bot.services.admin_service import (
    get_test_by_code,
    create_test_with_questions,
    get_admin_tests,
    toggle_test_status,
    delete_test_by_id,
    is_admin,
    get_test_details_admin,
    update_test_with_questions,
    get_test_participants_stats,
)
from bot.services.test_service import (
    get_or_create_user,
    get_user_by_telegram_id,
    update_user_profile,
    start_new_attempt,
    save_answer,
    finish_attempt,
    get_default_test,
)
from bot.services.report_service import generate_result_report, generate_teacher_notification
from bot.services.certificate_service import generate_certificate_image
from bot.services.attempt_service import process_test_submission
from bot.core.validator import check_open_answer
from bot.core.rate_limiter import RateLimitMiddleware
from bot.core.security import create_student_session_token, verify_student_session_token
from bot.web_app.auth import require_admin_user
from aiogram.types import FSInputFile

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def get_html_path(filename: str) -> Path:
    """Faylni web/ yoki root (.) papkasidan qidirish"""
    for candidate in [Path("web") / filename, Path(filename)]:
        if candidate.exists():
            return candidate
    return Path(filename)

app = FastAPI(title="Milliy Sertifikat Matematika API & TMA")

# Xavfsizlik: Rate Limiting Middleware (DDoS va spamdan himoya)
app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rasmlar va Statik fayllarni ulash
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
if Path("web").exists():
    app.mount("/web", StaticFiles(directory="web"), name="web")
    app.mount("/static", StaticFiles(directory="web"), name="static")
    if (Path("web") / "css").exists():
        app.mount("/css", StaticFiles(directory="web/css"), name="css")
    if (Path("web") / "js").exists():
        app.mount("/js", StaticFiles(directory="web/js"), name="js")


# Pydantic modellar
class SubmitAnswerItem(BaseModel):
    question_id: int
    user_answer: Optional[str] = ""
    sub_part_label: Optional[str] = None
    open_sub_key: Optional[str] = None
    answer_text: Optional[str] = ""


class SubmitTestRequest(BaseModel):
    test_id: int
    telegram_id: int
    full_name: str
    username: Optional[str] = None
    answers: List[SubmitAnswerItem]
    session_token: Optional[str] = None


class CreateSessionRequest(BaseModel):
    telegram_id: int
    test_id: int


class UpdateProfileRequest(BaseModel):
    telegram_id: int
    full_name: str
    phone_number: Optional[str] = None



class CreateQuestionItem(BaseModel):
    order_no: int
    type: str  # Y-1, Guruhlangan, O
    section: Optional[str] = "Algebra"
    difficulty_b: Optional[float] = 0.0
    text: Optional[str] = ""
    image_url: Optional[str] = None
    options: Optional[Dict[str, str]] = None
    correct_answer: Optional[str] = None
    sub_questions: Optional[List[Dict[str, Any]]] = None


class CreateTestPayload(BaseModel):
    creator_telegram_id: Optional[int] = None
    code: str
    title: str
    description: Optional[str] = ""
    subject: Optional[str] = "Matematika"
    time_limit_min: int = 150
    questions: List[Dict[str, Any]]
    grouped_context: Optional[Dict[str, Any]] = None
    test_type: Optional[str] = "permanent"
    access_type: Optional[str] = "closed"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    auto_check: Optional[bool] = True
    hide_answers: Optional[bool] = False
    required_channel: Optional[str] = None


# ==================== PUBLIC API: TEST TOPSHIRISH ====================

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = get_html_path("index.html")
    if index_file.exists():
        return FileResponse(
            index_file,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        )
    return HTMLResponse("<h1>Milliy Sertifikat Matematika WebApp ishga tushdi</h1>")


@app.get("/admin", response_class=HTMLResponse)
async def serve_admin():
    admin_file = get_html_path("admin.html")
    if admin_file.exists():
        return FileResponse(
            admin_file,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        )
    return HTMLResponse("<h1>Admin Panel</h1>")


@app.get("/healthz")
async def healthz():
    """
    DevOps va Monitoring uchun Salomatlik tekshiruvi (Healthcheck).
    Ma'lumotlar bazasi aloqasini tekshiradi va HTTP 200 yoki 503 qaytaradi.
    """
    db_connected = False
    try:
        async with async_session_maker() as session:
            await session.execute(select(1))
            db_connected = True
    except Exception as e:
        logger.error(f"Healthcheck: DB ulanishida xatolik: {e}")

    status_code = 200 if db_connected else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if db_connected else "unhealthy",
            "database": "connected" if db_connected else "disconnected",
            "service": "MSBot API",
            "version": "2.0.0",
            "timestamp": int(time.time()),
        },
    )


@app.get("/api/test/{code}")
async def api_get_test(code: str):
    """Test ma'lumotlari va barcha 45 ta savolni olish"""
    test = await get_test_by_code(code)
    if not test and code.upper() == "STANDART":
        test = await get_default_test()

    if not test:
        raise HTTPException(status_code=404, detail="Test topilmadi")

    # Savollarni guruhlari bilan birga yig'ish
    questions_data = []
    for q in test.questions:
        q_item = {
            "id": q.id,
            "order_no": q.order_no,
            "type": q.type,
            "section": q.section,
            "text": q.text,
            "image_url": q.image_url,
            "options": q.options,
            "sub_parts": q.sub_parts,
            "group_context": q.group.shared_context_text if q.group else None,
            "group_image_url": q.group.shared_image_url if q.group else None,
            "group_options": q.group.shared_options if q.group else None,
        }
        questions_data.append(q_item)

    # order_no bo'yicha saralash
    questions_data.sort(key=lambda x: x["order_no"])

    return {
        "id": test.id,
        "code": test.code,
        "title": test.title,
        "description": test.description,
        "question_count": test.question_count,
        "time_limit_min": test.time_limit_min,
        "hide_answers": getattr(test, "hide_answers", False),
        "questions": questions_data,
    }


@app.get("/api/user/{telegram_id}")
async def api_get_user(telegram_id: int):
    """Foydalanuvchining botda ro'yxatdan o'tganligini va adminlik huquqini tekshirish"""
    user = await get_user_by_telegram_id(telegram_id)
    admin_status = await is_admin(telegram_id)
    if not user:
        return {
            "registered": False,
            "full_name": None,
            "phone_number": None,
            "is_admin": admin_status,
        }
    return {
        "registered": bool(user.phone_number),
        "full_name": user.full_name,
        "phone_number": user.phone_number,
        "is_admin": admin_status,
    }


@app.post("/api/user/update-profile")
async def api_update_user_profile(payload: UpdateProfileRequest):
    """Talabgor ism-familiyasini Web App orqali yangilash"""
    clean_name = payload.full_name.strip()
    clean_letters = ''.join(c for c in clean_name if c.isalpha())
    if len(clean_letters) < 3:
        raise HTTPException(status_code=400, detail="Ism kamida 3 ta harfdan iborat bo'lishi kerak.")
    
    await update_user_profile(
        telegram_id=payload.telegram_id,
        full_name=clean_name,
        phone_number=payload.phone_number,
    )
    return {"success": True, "full_name": clean_name}



@app.post("/api/test/session")
async def api_create_session(payload: CreateSessionRequest):
    """
    Talabaning test topshirish sessiyasi uchun HMAC-SHA256 bilan imzolangan token yaratish.
    Ushbu token soxtalashtirish (spoofing) va birovning nomidan topshirishning oldini oladi.
    """
    token = create_student_session_token(payload.telegram_id, payload.test_id)
    return {
        "success": True,
        "session_token": token,
        "expires_in_seconds": 18000,
    }


@app.post("/api/test/submit")
async def api_submit_test(
    payload: SubmitTestRequest,
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
):
    """
    Test javoblarini topshirish, RASH (IRT) modeli bo'yicha baholash
    va natijani Telegram bot orqali foydalanuvchiga yuborish.
    Sessiya tokeni uzatilgan bo'lsa, HMAC imzosi va muddati tekshiriladi.
    """
    token_to_check = x_session_token or payload.session_token
    if token_to_check:
        is_valid, token_payload, err_msg = verify_student_session_token(token_to_check)
        if not is_valid or not token_payload:
            raise HTTPException(status_code=401, detail=err_msg or "Sessiya tokeni yaroqsiz.")
        if token_payload.get("tg_id") != payload.telegram_id or token_payload.get("test_id") != payload.test_id:
            raise HTTPException(status_code=403, detail="Sessiya tokeni foydalanuvchi yoki testga mos emas.")

    bot = getattr(app.state, "bot", None)
    result = await process_test_submission(
        test_id=payload.test_id,
        telegram_id=payload.telegram_id,
        full_name=payload.full_name,
        username=payload.username,
        answers=payload.answers,
        bot=bot,
    )
    return result


# ==================== ADMIN API: RASM VA TEST YUKLASH ====================

@app.post("/api/admin/upload-image")
async def api_upload_image(
    file: UploadFile = File(...),
    admin_telegram_id: int = Depends(require_admin_user),
):
    """Savol uchun rasm (chizma, formula grafikasi) yuklash — HEIC/HEIF avtomatik konvertatsiya bilan"""
    ext = Path(file.filename or "").suffix.lower()
    raw_content = await file.read()

    # 1. HEIC / HEIF (iPhone suratlari) tekshiruvi
    is_heic = (
        ext in [".heic", ".heif"]
        or b"ftypheic" in raw_content[:32]
        or b"ftypmif1" in raw_content[:32]
    )

    if is_heic:
        try:
            import pillow_heif
            from PIL import Image
            heif_file = pillow_heif.read_heif(raw_content)
            img = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw")
            filename = f"{uuid.uuid4().hex}.png"
            filepath = UPLOAD_DIR / filename
            img.save(filepath, "PNG")
            return {"url": f"/uploads/{filename}", "filename": filename}
        except Exception:
            pass

    # 2. Standart web formatlar (png, jpg, jpeg, webp, svg)
    if ext in [".png", ".jpg", ".jpeg", ".webp", ".svg"]:
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = UPLOAD_DIR / filename
        with open(filepath, "wb") as f:
            f.write(raw_content)
        return {"url": f"/uploads/{filename}", "filename": filename}

    # 3. Boshqa har qanday formatni PIL bilan PNG ga saqlash
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(raw_content))
        filename = f"{uuid.uuid4().hex}.png"
        filepath = UPLOAD_DIR / filename
        img.save(filepath, "PNG")
        return {"url": f"/uploads/{filename}", "filename": filename}
    except Exception:
        filename = f"{uuid.uuid4().hex}.png"
        filepath = UPLOAD_DIR / filename
        with open(filepath, "wb") as f:
            f.write(raw_content)
        return {"url": f"/uploads/{filename}", "filename": filename}


@app.post("/api/admin/create-test")
async def api_create_test(
    payload: CreateTestPayload,
    admin_telegram_id: int = Depends(require_admin_user),
):
    """Admin tomonidan yangi test yaratish (haqiqiy tasdiqlangan admin_telegram_id ishlatiladi)"""
    admin_user = await get_or_create_user(admin_telegram_id, "Admin")

    if payload.time_limit_min <= 0:
        raise HTTPException(status_code=400, detail="Vaqt chegarasi kamida 1 daqiqa bo'lishi kerak.")

    success, msg, test_obj = await create_test_with_questions(
        creator_user_id=admin_user.id,
        code=payload.code,
        title=payload.title,
        description=payload.description or "",
        time_limit_min=max(1, payload.time_limit_min),
        questions_data=payload.questions,
        grouped_context=payload.grouped_context,
        hide_answers=payload.hide_answers or False,
    )

    if not success or not test_obj:
        raise HTTPException(status_code=400, detail=msg)

    return {
        "success": True,
        "message": msg,
        "test_id": test_obj.id,
        "code": test_obj.code,
        "question_count": test_obj.question_count,
    }


@app.get("/api/admin/tests/{telegram_id}")
async def api_get_admin_tests(
    telegram_id: int,
    admin_telegram_id: int = Depends(require_admin_user),
):
    """Admin o'z testlari statistikasini olish (tasdiqlangan admin_telegram_id bo'yicha)"""
    user = await get_or_create_user(admin_telegram_id, "Admin")
    tests = await get_admin_tests(user.id)
    return {"tests": tests}


@app.post("/api/admin/tests/{test_id}/toggle")
async def api_toggle_test(
    test_id: int,
    admin_telegram_id: int = Depends(require_admin_user),
):
    """Test faolligini o'zgartirish (faol / to'xtatilgan)"""
    success, msg, is_active = await toggle_test_status(test_id)
    if not success:
        raise HTTPException(status_code=404, detail=msg)
    return {"success": True, "message": msg, "is_active": is_active}


class UpdateTestPayload(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    time_limit_min: Optional[int] = None
    questions: Optional[List[Dict[str, Any]]] = None
    grouped_context: Optional[Dict[str, Any]] = None
    hide_answers: Optional[bool] = None


@app.delete("/api/admin/tests/{test_id}")
async def api_delete_test(
    test_id: int,
    admin_telegram_id: int = Depends(require_admin_user),
):
    """Testni o'chirish"""
    success, msg = await delete_test_by_id(test_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@app.get("/api/admin/test-details/{test_id}")
async def api_get_admin_test_details(
    test_id: int,
    admin_telegram_id: int = Depends(require_admin_user),
):
    """Admin uchun testning barcha savollari va to'g'ri javob kalitlarini olish"""
    user = await get_or_create_user(admin_telegram_id, "Admin")
    details = await get_test_details_admin(test_id, user.id)
    if not details:
        raise HTTPException(status_code=404, detail="Test topilmadi yoki ko'rishga ruxsat yo'q")
    return {"test": details}


@app.put("/api/admin/tests/{test_id}")
@app.post("/api/admin/tests/{test_id}/update")
async def api_update_admin_test(
    test_id: int,
    payload: UpdateTestPayload,
    admin_telegram_id: int = Depends(require_admin_user),
):
    """Test va uning javob kalitlarini tahrirlash/saqlash"""
    user = await get_or_create_user(admin_telegram_id, "Admin")
    success, msg = await update_test_with_questions(
        test_id=test_id,
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        time_limit_min=payload.time_limit_min,
        questions_data=payload.questions,
        grouped_context=payload.grouped_context,
        hide_answers=payload.hide_answers,
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@app.get("/api/admin/tests/{test_id}/stats")
async def api_get_test_stats(
    test_id: int,
    admin_telegram_id: int = Depends(require_admin_user),
):
    """Test qatnashuvchilari va batafsil natijalar statistikasini olish"""
    user = await get_or_create_user(admin_telegram_id, "Admin")
    stats = await get_test_participants_stats(test_id, user.id)
    if not stats:
        raise HTTPException(status_code=404, detail="Test topilmadi yoki statistikani ko'rishga ruxsat yo'q")
    return stats


