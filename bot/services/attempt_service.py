"""
Test topshirish va natijalarni qayta ishlash xizmati (Attempt Service).
Rasch modeli, sertifikat blankasi generatsiyasi va xabarnomalar yuborish mantiqini birlashtiradi.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.database.session import async_session_maker
from bot.database.models import Test, User, Attempt, AttemptAnswer
from bot.services.test_service import (
    get_or_create_user,
    start_new_attempt,
    save_answer,
    finish_attempt,
)
from bot.services.report_service import generate_result_report, generate_teacher_notification
from bot.services.certificate_service import generate_certificate_image
from aiogram.types import FSInputFile

logger = logging.getLogger(__name__)


async def process_test_submission(
    test_id: int,
    telegram_id: int,
    full_name: str,
    username: Optional[str],
    answers: List[Any],
    bot: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Test javoblarini topshirish, Rasch (IRT) modeli orqali hisoblash,
    sertifikat yaratish va Telegram orqali xabarnomalarni tarqatish.
    """
    # 1. Foydalanuvchini olish yoki ro'yxatdan o'tkazish
    user = await get_or_create_user(
        telegram_id=telegram_id,
        full_name=full_name,
        username=username,
    )

    # 2. Urinishni boshlash va javoblarni saqlash
    attempt = await start_new_attempt(user.id, test_id)
    for ans in answers:
        q_id = getattr(ans, "question_id", ans.get("question_id") if isinstance(ans, dict) else None)
        u_ans = getattr(ans, "user_answer", ans.get("user_answer") if isinstance(ans, dict) else "")
        sub_part = getattr(ans, "sub_part_label", ans.get("sub_part_label") if isinstance(ans, dict) else None)
        if q_id:
            await save_answer(
                attempt_id=attempt.id,
                question_id=q_id,
                user_answer=u_ans,
                is_correct=False,
                sub_part_label=sub_part,
            )

    # 3. Urinishni yakunlash va Rasch modelida baholash
    completed_attempt, rasch_result = await finish_attempt(attempt.id)

    # 4. Test ma'lumotlarini yuklash
    test_obj = None
    try:
        async with async_session_maker() as session:
            stmt = select(Test).where(Test.id == test_id)
            res = await session.execute(stmt)
            test_obj = res.scalar_one_or_none()
    except Exception as e:
        logger.warning(f"Test obyektini yuklashda xatolik: {e}")

    hide_answers = getattr(test_obj, "hide_answers", False) if test_obj else False

    # 5. Sertifikat blankasini generatsiya qilish
    cert_url = None
    cert_file_path = None
    try:
        cert_file_path = generate_certificate_image(
            attempt_id=completed_attempt.id,
            telegram_id=telegram_id,
            full_name=full_name or user.full_name or "Talabgor",
            final_score=rasch_result.final_score,
            grade=rasch_result.grade,
            is_certified=rasch_result.is_certified,
            subject="Matematika",
            finished_at=completed_attempt.finished_at,
        )
        cert_url = f"/uploads/certificates/cert_{completed_attempt.id}.jpg"
    except Exception as e:
        logger.error(f"Sertifikat rasmini yaratishda xatolik: {e}", exc_info=True)

    # 6. Telegram bot orqali bildirishnomalar yuborish
    if bot:
        # A. Talabgorga natija yuborish
        if telegram_id:
            try:
                if hide_answers:
                    test_title = test_obj.title if test_obj else "Milliy Sertifikat"
                    await bot.send_message(
                        chat_id=telegram_id,
                        text=(
                            "✅ <b>Test muvaffaqiyatli yakunlandi!</b>\n\n"
                            f"🏷 <b>Test:</b> {test_title}\n"
                            "📥 Sizning barcha javoblaringiz qabul qilindi.\n\n"
                            "🔒 <i>Ushbu testda natijalar yashirilgan. Natijalarni ustozingiz e'lon qiladi.</i>"
                        ),
                        parse_mode="HTML",
                    )
                else:
                    if cert_file_path and os.path.exists(cert_file_path):
                        cert_status = "Sertifikat berilsin" if rasch_result.is_certified else "Sertifikat berilmadi"
                        cert_grade = rasch_result.grade if rasch_result.is_certified else "Talabga javob bermadi"
                        percent = min(100.0, max(0.0, (rasch_result.final_score / 70.0) * 100.0))
                        caption = (
                            f"📄 <b>Umumta'lim fanini bilish darajasi to'g'risida sertifikat</b>\n\n"
                            f"👤 <b>Talabgor:</b> {full_name or user.full_name}\n"
                            f"📊 <b>To'plangan ball:</b> {rasch_result.final_score:.1f} ball ({percent:.1f}%)\n"
                            f"🎖 <b>Daraja:</b> {cert_grade}\n"
                            f"📋 <b>Xulosa:</b> {cert_status}"
                        )
                        await bot.send_photo(
                            chat_id=telegram_id,
                            photo=FSInputFile(cert_file_path),
                            caption=caption,
                            parse_mode="HTML",
                        )

                    report = generate_result_report(user, completed_attempt, rasch_result)
                    await bot.send_message(
                        chat_id=telegram_id,
                        text=report,
                        parse_mode="HTML",
                    )
            except Exception as e:
                logger.warning(f"Talabgorga xabar yuborishda ogohlantirish: {e}")

        # B. Test muallifiga (o'qituvchiga) bildirishnoma yuborish
        try:
            if test_obj and test_obj.created_by_user_id:
                async with async_session_maker() as session:
                    creator = await session.get(User, test_obj.created_by_user_id)
                    if creator and creator.telegram_id:
                        if cert_file_path and os.path.exists(cert_file_path):
                            t_caption = (
                                f"📋 <b>O'quvchi natijasi va sertifikati:</b>\n"
                                f"👤 <b>Talabgor:</b> {full_name or user.full_name}\n"
                                f"🏷 <b>Test:</b> {test_obj.title} (#{test_obj.code})\n"
                                f"📊 <b>Ball:</b> {rasch_result.final_score:.1f} / 70 ({rasch_result.grade if rasch_result.is_certified else 'Talabga javob bermadi'})\n"
                                f"📌 <b>Holat:</b> {'Sertifikat berilsin' if rasch_result.is_certified else 'Sertifikat berilmadi'}"
                            )
                            await bot.send_photo(
                                chat_id=creator.telegram_id,
                                photo=FSInputFile(cert_file_path),
                                caption=t_caption,
                                parse_mode="HTML",
                            )

                        t_report = generate_teacher_notification(user, completed_attempt, rasch_result, test_obj)
                        await bot.send_message(
                            chat_id=creator.telegram_id,
                            text=t_report,
                            parse_mode="HTML",
                        )
        except Exception as e:
            logger.warning(f"O'qituvchiga xabar yuborishda ogohlantirish: {e}")

    # Savollar tafsilotini tuzish
    questions_detail = []
    if not hide_answers:
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
                    questions_detail.append({
                        "question_id": a.question_id,
                        "order_no": a.question.order_no if a.question else None,
                        "type": a.question.type if a.question else None,
                        "sub_part_label": a.sub_part_label,
                        "sub_part": a.sub_part_label,
                        "user_answer": a.user_answer,
                        "correct_answer": a.question.correct_answer if a.question else None,
                        "is_correct": a.is_correct,
                    })
        except Exception as e:
            logger.warning(f"Tafsilotlarni yuklashda xatolik: {e}")

    if hide_answers:
        return {
            "success": True,
            "attempt_id": completed_attempt.id,
            "hide_answers": True,
            "message": "Test muvaffaqiyatli yakunlandi! Natijalarni ustozingiz e'lon qiladi.",
        }

    return {
        "success": True,
        "attempt_id": completed_attempt.id,
        "hide_answers": False,
        "raw_score": rasch_result.raw_score,
        "total_items": rasch_result.total_items,
        "theta": rasch_result.theta,
        "standard_error": rasch_result.standard_error,
        "sem": rasch_result.standard_error,
        "final_score": rasch_result.final_score,
        "grade": rasch_result.grade,
        "is_certified": rasch_result.is_certified,
        "certificate_url": cert_url if rasch_result.is_certified else None,
        "details": questions_detail,
        "questions_detail": questions_detail,
        "message": "Test muvaffaqiyatli topshirildi.",
    }
