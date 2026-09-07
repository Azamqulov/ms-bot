"""
FastAPI Web App va REST API moduli:
Telegram Mini App (TMA) va Admin Web Konstruktori uchun.
"""

import os
import shutil
import uuid
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
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
)
from bot.services.test_service import (
    get_or_create_user,
    get_user_by_telegram_id,
    start_new_attempt,
    save_answer,
    finish_attempt,
    get_default_test,
)
from bot.services.report_service import generate_result_report, generate_teacher_notification
from bot.core.validator import check_open_answer
from bot.web_app.auth import require_admin_user

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def get_html_path(filename: str) -> Path:
    """Faylni root (.) yoki web/ papkasidan qidirish"""
    for candidate in [Path(filename), Path("web") / filename]:
        if candidate.exists():
            return candidate
    return Path(filename)

app = FastAPI(title="Milliy Sertifikat Matematika API & TMA")

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
    app.mount("/static", StaticFiles(directory="web"), name="static")


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


@app.post("/api/test/submit")
async def api_submit_test(payload: SubmitTestRequest):
    """
    Test javoblarini topshirish, RASH (IRT) modeli bo'yicha baholash
    va natijani Telegram bot orqali foydalanuvchiga yuborish.
    """
    user = await get_or_create_user(
        telegram_id=payload.telegram_id,
        full_name=payload.full_name,
        username=payload.username,
    )

    attempt = await start_new_attempt(user.id, payload.test_id)

    # Savollarni yuklash (to'g'ri javoblar bilan solishtirish uchun)
    for ans in payload.answers:
        await save_answer(
            attempt_id=attempt.id,
            question_id=ans.question_id,
            user_answer=ans.user_answer,
            is_correct=False, # finish_attempt to'liq qayta tekshiradi
            sub_part_label=ans.sub_part_label,
        )

    completed_attempt, rasch_result = await finish_attempt(attempt.id)

    # Natijani avtomatik Telegram Bot orqali yuborish
    bot = getattr(app.state, "bot", None)
    if bot:
        # 1. Talabgorning o'ziga to'liq natija xabarini yuborish
        if payload.telegram_id:
            try:
                report_text = generate_result_report(user, completed_attempt, rasch_result)
                await bot.send_message(
                    chat_id=payload.telegram_id,
                    text=report_text,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Telegram orqali talabgorga natija yuborishda ogohlantirish: {e}")

        # 2. Test yaratgan odam (muallif / o'qituvchi) ning telegramiga natijani yuborish
        try:
            async with async_session_maker() as session:
                t_stmt = select(Test).where(Test.id == payload.test_id)
                t_res = await session.execute(t_stmt)
                test_obj = t_res.scalar_one_or_none()
                if test_obj and test_obj.created_by_user_id:
                    c_user = await session.get(User, test_obj.created_by_user_id)
                    if c_user and c_user.telegram_id:
                        teacher_text = generate_teacher_notification(
                            student=user,
                            test_title=test_obj.title,
                            test_code=test_obj.code,
                            attempt=completed_attempt,
                            rasch_result=rasch_result
                        )
                        await bot.send_message(
                            chat_id=c_user.telegram_id,
                            text=teacher_text,
                            parse_mode="HTML"
                        )
                        logger.info(f"Natija test yaratuvchisi ({c_user.telegram_id}) ga muvaffaqiyatli yuborildi.")
        except Exception as e:
            logger.warning(f"Test yaratuvchisiga Telegram orqali natija yuborishda ogohlantirish: {e}")

    detailed_results = []
    try:
        async with async_session_maker() as session:
            ans_stmt = (
                select(AttemptAnswer)
                .options(selectinload(AttemptAnswer.question))
                .where(AttemptAnswer.attempt_id == completed_attempt.id)
                .order_by(AttemptAnswer.id)
            )
            ans_res = await session.execute(ans_stmt)
            for a in ans_res.scalars().all():
                detailed_results.append({
                    "question_id": a.question_id,
                    "order_no": a.question.order_no if a.question else None,
                    "sub_part_label": a.sub_part_label,
                    "user_answer": a.user_answer,
                    "is_correct": a.is_correct,
                })
    except Exception as e:
        logger.warning(f"Detailed results fetch error: {e}")

    return {
        "attempt_id": completed_attempt.id,
        "raw_score": rasch_result.raw_score,
        "total_items": rasch_result.total_items,
        "theta": rasch_result.theta,
        "standard_error": rasch_result.standard_error,
        "final_score": rasch_result.final_score,
        "grade": rasch_result.grade,
        "is_certified": rasch_result.is_certified,
        "details": detailed_results,
    }


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


