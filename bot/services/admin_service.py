"""
Admin va Super Admin boshqaruv servisi hamda Test yuklash logikasi.
"""

import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from bot.config import settings
from bot.database.session import async_session_maker
from bot.database.models import User, Test, Question, QuestionGroup, Attempt, AttemptAnswer

logger = logging.getLogger(__name__)


def is_super_admin(telegram_id: int) -> bool:
    """Foydalanuvchi Super Adminmi?"""
    return telegram_id == settings.SUPER_ADMIN_ID


async def ensure_super_admin() -> None:
    """Super adminni bazada avtomatik ro'yxatdan o'tkazish/tasdiqlash"""
    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == settings.SUPER_ADMIN_ID)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=settings.SUPER_ADMIN_ID,
                full_name="Bosh Super Admin",
                role="super_admin",
            )
            session.add(user)
            await session.commit()
        else:
            if user.role != "super_admin":
                user.role = "super_admin"
                await session.commit()


async def is_admin(telegram_id: int) -> bool:
    """Foydalanuvchi Admin yoki Super Adminmi?"""
    if is_super_admin(telegram_id):
        return True

    if telegram_id in settings.admin_ids_list:
        return True

    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        return user is not None and user.role in ("admin", "super_admin")


async def add_admin(target_telegram_id: int) -> Tuple[bool, str]:
    """Super admin tomonidan yangi admin qo'shish"""
    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == target_telegram_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            # Agar hali /start bosmagan bo'lsa ham admin sifatida kiritib qo'yamiz
            user = User(
                telegram_id=target_telegram_id,
                full_name=f"Admin {target_telegram_id}",
                role="admin",
            )
            session.add(user)
        else:
            if user.role == "super_admin":
                return False, "Bu foydalanuvchi allaqachon Super Admin!"
            user.role = "admin"

        await session.commit()
        return True, f"Foydalanuvchi ({target_telegram_id}) muvaffaqiyatli Admin qilindi!"


async def remove_admin(target_telegram_id: int) -> Tuple[bool, str]:
    """Adminlikdan mahrum qilish"""
    if target_telegram_id == settings.SUPER_ADMIN_ID:
        return False, "Super Adminni o'chirib bo'lmaydi!"

    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == target_telegram_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user or user.role != "admin":
            return False, "Ushbu foydalanuvchi adminlar ro'yxatida topilmadi."

        user.role = "user"
        await session.commit()
        return True, f"Admin ({target_telegram_id}) muvaffaqiyatli oddiy foydalanuvchi holatiga o'tkazildi."


async def get_all_admins() -> List[User]:
    """Barcha adminlar va super adminlar ro'yxati"""
    async with async_session_maker() as session:
        stmt = select(User).where(User.role.in_(["admin", "super_admin"])).order_by(User.id)
        res = await session.execute(stmt)
        admins = list(res.scalars().all())

        # Agar super admin bazada bo'lmasa, uni ham ko'rsatish
        has_super = any(a.telegram_id == settings.SUPER_ADMIN_ID for a in admins)
        if not has_super:
            super_u = User(
                telegram_id=settings.SUPER_ADMIN_ID,
                full_name="Bosh Super Admin",
                role="super_admin"
            )
            admins.insert(0, super_u)

        return admins


async def create_test_with_questions(
    creator_user_id: int,
    code: str,
    title: str,
    description: str,
    time_limit_min: int,
    questions_data: List[Dict[str, Any]],
    grouped_context: Optional[Dict[str, Any]] = None,
    hide_answers: bool = False,
) -> Tuple[bool, str, Optional[Test]]:
    """
    Admin tomonidan yangi test va uning savollarini bazaga yuklash.
    """
    clean_code = code.strip().upper().replace(" ", "_")
    if not clean_code:
        return False, "Test kodi bo'sh bo'lishi mumkin emas.", None

    if not questions_data:
        return False, "Savollar ro'yxati bo'sh bo'lishi mumkin emas.", None

    async with async_session_maker() as session:
        # Kod band emasligini tekshirish (katta-kichik harf farqsiz qat'iy tekshirish)
        stmt = select(Test).where(func.upper(Test.code) == clean_code)
        res = await session.execute(stmt)
        if res.scalar_one_or_none():
            return False, f"'{clean_code}' kodi allaqachon mavjud! Boshqa kod tanlang.", None

        new_test = Test(
            code=clean_code,
            title=title.strip(),
            description=description.strip() if description else None,
            question_count=len(questions_data),
            time_limit_min=time_limit_min,
            created_by_user_id=creator_user_id,
            is_active=True,
            hide_answers=hide_answers,
        )
        session.add(new_test)
        await session.flush()

        # Guruhlangan kontekst bo'lsa
        group_id = None
        if grouped_context:
            shared_text = grouped_context.get("shared_context_text", "")
            shared_img = grouped_context.get("shared_image_url")
            shared_opts = grouped_context.get("shared_options", {})
            if shared_text or shared_img or shared_opts:
                q_group = QuestionGroup(
                    test_id=new_test.id,
                    shared_context_text=shared_text or "33–35-savollar uchun umumiy shart:",
                    shared_image_url=shared_img,
                    shared_options=shared_opts,
                )
                session.add(q_group)
                await session.flush()
                group_id = q_group.id

        # Savollarni qo'shish
        for idx, q_item in enumerate(questions_data, start=1):
            q_type = q_item.get("type", "Y-1")
            q_obj = Question(
                test_id=new_test.id,
                group_id=group_id if q_type == "GROUPED" else None,
                order_no=q_item.get("order_no", idx),
                type=q_type,
                section=q_item.get("section", "Matematika"),
                difficulty_b=float(q_item.get("difficulty_b", 0.0)),
                text=q_item.get("text", f"Savol {idx}"),
                image_url=q_item.get("image_url"),
                options=q_item.get("options"),
                sub_parts=q_item.get("sub_parts"),
                correct_answer=q_item.get("correct_answer"),
            )
            session.add(q_obj)

        try:
            await session.commit()
            await session.refresh(new_test)
            return True, f"Test muvaffaqiyatli yuklandi! Kod: {clean_code}", new_test
        except Exception as e:
            await session.rollback()
            err_msg = str(e)
            if "UNIQUE constraint" in err_msg or "duplicate key" in err_msg or "tests_code_key" in err_msg:
                return False, f"'{clean_code}' kodi allaqachon mavjud! Boshqa kod tanlang.", None
            return False, f"Ma'lumotlar bazasida xatolik yuz berdi: {err_msg}", None


async def get_test_by_code(code: str) -> Optional[Test]:
    """Testni unikal kodi bo'yicha topish"""
    clean_code = code.strip().upper().replace(" ", "_")
    async with async_session_maker() as session:
        stmt = (
            select(Test)
            .options(
                selectinload(Test.questions).selectinload(Question.group)
            )
            .where(Test.code == clean_code, Test.is_active == True)
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()


async def get_admin_tests(creator_user_id: int) -> List[Dict[str, Any]]:
    """Admin yaratgan testlar va ular bo'yicha statistika"""
    async with async_session_maker() as session:
        user_stmt = select(User).where(User.id == creator_user_id)
        user_res = await session.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        # Agar super admin bo'lsa yoki barcha testlarni ko'rish ruxsati bo'lsa
        if user and user.role == "super_admin":
            stmt = select(Test).order_by(Test.id.desc())
        else:
            stmt = select(Test).where(Test.created_by_user_id == creator_user_id).order_by(Test.id.desc())

        res = await session.execute(stmt)
        tests = res.scalars().all()

        results = []
        for t in tests:
            # Qatnashganlar soni
            att_stmt = select(func.count(Attempt.id)).where(Attempt.test_id == t.id)
            att_count = (await session.execute(att_stmt)).scalar() or 0

            # O'rtacha ball
            avg_stmt = select(func.avg(Attempt.final_score)).where(Attempt.test_id == t.id, Attempt.status == "completed")
            avg_score = (await session.execute(avg_stmt)).scalar() or 0.0

            results.append({
                "id": t.id,
                "code": t.code,
                "title": t.title,
                "description": t.description or "",
                "question_count": t.question_count,
                "time_limit_min": t.time_limit_min,
                "is_active": t.is_active,
                "created_at": t.created_at.strftime("%d.%m.%Y %H:%M") if t.created_at else "",
                "attempts_count": att_count,
                "avg_score": round(float(avg_score), 1),
            })
        return results


async def toggle_test_status(test_id: int) -> Tuple[bool, str, bool]:
    """Test holatini faol/nofaol qilish"""
    async with async_session_maker() as session:
        stmt = select(Test).where(Test.id == test_id)
        res = await session.execute(stmt)
        test = res.scalar_one_or_none()
        if not test:
            return False, "Test topilmadi", False
        test.is_active = not test.is_active
        await session.commit()
        return True, f"Test holati {'faollashtirildi' if test.is_active else 'to‘xtatildi'}", test.is_active


async def delete_test_by_id(test_id: int) -> Tuple[bool, str]:
    """Testni o'chirish"""
    async with async_session_maker() as session:
        stmt = select(Test).where(Test.id == test_id)
        res = await session.execute(stmt)
        test = res.scalar_one_or_none()
        if not test:
            return False, "Test topilmadi"
        if test.code == "STANDART":
            return False, "Standart namuna testini o'chirib bo'lmaydi!"
        await session.delete(test)
        await session.commit()
        return True, "Test muvaffaqiyatli o'chirildi"


async def get_test_participants_stats(test_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Test bo'yicha barcha qatnashuvchilar natijalari va to'liq statistika"""
    async with async_session_maker() as session:
        user_stmt = select(User).where(User.id == user_id)
        user = (await session.execute(user_stmt)).scalar_one_or_none()

        test_stmt = select(Test).where(Test.id == test_id)
        test = (await session.execute(test_stmt)).scalar_one_or_none()
        if not test:
            return None

        # Ruxsat tekshiruvi: faqat o'z testi yoki super_admin
        is_user_super = (user and (user.role == "super_admin" or is_super_admin(user.telegram_id)))
        if user and not is_user_super and test.created_by_user_id != user_id:
            return None

        # Barcha urinishlarni olish (final_score bo'yicha kamayish tartibida)
        stmt = (
            select(Attempt)
            .options(selectinload(Attempt.user))
            .where(Attempt.test_id == test_id)
            .order_by(Attempt.final_score.desc().nullslast(), Attempt.started_at.desc())
        )
        attempts = (await session.execute(stmt)).scalars().all()

        participants = []
        total_score = 0.0
        completed_count = 0
        certified_count = 0
        highest_score = 0.0

        for idx, att in enumerate(attempts, 1):
            score = att.final_score or 0.0
            if att.status == "completed":
                total_score += score
                completed_count += 1
                if score > highest_score:
                    highest_score = score
                if att.is_certified:
                    certified_count += 1

            u = att.user
            participants.append({
                "rank": idx,
                "attempt_id": att.id,
                "user_id": u.id if u else None,
                "telegram_id": u.telegram_id if u else None,
                "full_name": u.full_name if u else "Noma'lum",
                "phone_number": u.phone_number if u else None,
                "username": u.username if u else None,
                "raw_score": att.raw_score,
                "final_score": round(float(score), 1),
                "grade": att.grade or "Baholanmagan",
                "is_certified": att.is_certified,
                "status": att.status,
                "started_at": att.started_at.strftime("%d.%m.%Y %H:%M") if att.started_at else "",
                "finished_at": att.finished_at.strftime("%d.%m.%Y %H:%M") if att.finished_at else "",
            })

        avg_score = round(float(total_score / completed_count), 1) if completed_count > 0 else 0.0

        return {
            "test_id": test.id,
            "test_code": test.code,
            "test_title": test.title,
            "question_count": test.question_count,
            "time_limit_min": test.time_limit_min,
            "total_participants": len(attempts),
            "completed_count": completed_count,
            "certified_count": certified_count,
            "avg_score": avg_score,
            "highest_score": round(float(highest_score), 1),
            "participants": participants,
        }



async def get_test_details_admin(test_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Admin uchun test ma'lumotlari, barcha savollar va to'g'ri javob kalitlarini qaytarish"""
    async with async_session_maker() as session:
        user_stmt = select(User).where(User.id == user_id)
        user = (await session.execute(user_stmt)).scalar_one_or_none()

        stmt = (
            select(Test)
            .options(
                selectinload(Test.questions).selectinload(Question.group),
                selectinload(Test.question_groups)
            )
            .where(Test.id == test_id)
        )
        res = await session.execute(stmt)
        test = res.scalar_one_or_none()
        if not test:
            return None

        # Ruxsat tekshiruvi: faqat o'z testi yoki super_admin
        is_user_super = (user and (user.role == "super_admin" or is_super_admin(user.telegram_id)))
        if user and not is_user_super and test.created_by_user_id != user_id:
            return None

        questions_data = []
        for q in test.questions:
            questions_data.append({
                "id": q.id,
                "order_no": q.order_no,
                "type": q.type,
                "section": q.section,
                "difficulty_b": q.difficulty_b,
                "text": q.text,
                "image_url": q.image_url,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "sub_parts": q.sub_parts,
                "group_id": q.group_id,
            })
        questions_data.sort(key=lambda x: x["order_no"])

        grouped_context = None
        if test.question_groups:
            grp = test.question_groups[0]
            grouped_context = {
                "id": grp.id,
                "shared_context_text": grp.shared_context_text,
                "shared_image_url": grp.shared_image_url,
                "shared_options": grp.shared_options,
            }

        return {
            "id": test.id,
            "code": test.code,
            "title": test.title,
            "description": test.description or "",
            "time_limit_min": test.time_limit_min,
            "question_count": test.question_count,
            "is_active": test.is_active,
            "hide_answers": getattr(test, "hide_answers", False),
            "questions": questions_data,
            "grouped_context": grouped_context,
        }


async def update_test_with_questions(
    test_id: int,
    user_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    time_limit_min: Optional[int] = None,
    questions_data: Optional[List[Dict[str, Any]]] = None,
    grouped_context: Optional[Dict[str, Any]] = None,
    hide_answers: Optional[bool] = None,
) -> Tuple[bool, str]:
    """Test ma'lumotlari va uning savollari/to'g'ri javob kalitlarini yangilash"""
    async with async_session_maker() as session:
        user_stmt = select(User).where(User.id == user_id)
        user = (await session.execute(user_stmt)).scalar_one_or_none()

        stmt = (
            select(Test)
            .options(
                selectinload(Test.questions),
                selectinload(Test.question_groups)
            )
            .where(Test.id == test_id)
        )
        test = (await session.execute(stmt)).scalar_one_or_none()
        if not test:
            return False, "Test topilmadi"

        if user and user.role != "super_admin" and test.created_by_user_id != user_id:
            return False, "Sizda ushbu testni tahrirlash huquqi yo'q"

        if title:
            test.title = title.strip()
        if description is not None:
            test.description = description.strip() if description else None
        if time_limit_min is not None and time_limit_min > 0:
            test.time_limit_min = time_limit_min
        if hide_answers is not None:
            test.hide_answers = hide_answers

        # Guruh kontekstini yangilash
        if grouped_context and test.question_groups:
            grp = test.question_groups[0]
            if "shared_context_text" in grouped_context:
                grp.shared_context_text = grouped_context["shared_context_text"]
            if "shared_image_url" in grouped_context:
                grp.shared_image_url = grouped_context["shared_image_url"]
            if "shared_options" in grouped_context:
                grp.shared_options = grouped_context["shared_options"]

        # Savollar kalitlarini / ma'lumotlarini yangilash
        if questions_data:
            q_map = {q.order_no: q for q in test.questions}
            for q_in in questions_data:
                order_no = q_in.get("order_no")
                if order_no in q_map:
                    q_obj = q_map[order_no]
                    if "correct_answer" in q_in:
                        q_obj.correct_answer = q_in["correct_answer"]
                    if "sub_parts" in q_in:
                        q_obj.sub_parts = q_in["sub_parts"]
                    if "text" in q_in and q_in["text"]:
                        q_obj.text = q_in["text"]
                    if "options" in q_in and q_in["options"]:
                        q_obj.options = q_in["options"]
                    if "difficulty_b" in q_in and q_in["difficulty_b"] is not None:
                        q_obj.difficulty_b = float(q_in["difficulty_b"])
                    if "image_url" in q_in:
                        q_obj.image_url = q_in["image_url"]
                    if "section" in q_in and q_in["section"]:
                        q_obj.section = q_in["section"]

        await session.commit()
        return True, "Test muvaffaqiyatli yangilandi!"


async def get_attempt_detailed_answers(attempt_id: int, admin_user_id: int) -> Optional[Dict[str, Any]]:
    """Talabgorning ma'lum bir urinishi bo'yicha har bir savol javobi tahlilini olish"""
    async with async_session_maker() as session:
        user_stmt = select(User).where(User.id == admin_user_id)
        admin_user = (await session.execute(user_stmt)).scalar_one_or_none()

        att_stmt = (
            select(Attempt)
            .options(
                selectinload(Attempt.user),
                selectinload(Attempt.test).selectinload(Test.questions),
                selectinload(Attempt.answers),
            )
            .where(Attempt.id == attempt_id)
        )
        att = (await session.execute(att_stmt)).scalar_one_or_none()
        if not att or not att.test:
            return None

        # Ruxsat tekshiruvi: faqat test egasi yoki super admin
        is_super = admin_user and (admin_user.role == "super_admin" or is_super_admin(admin_user.telegram_id))
        if admin_user and not is_super and att.test.created_by_user_id != admin_user_id:
            return None

        # Savollar tartibi bo'yicha tartiblash
        questions = sorted(att.test.questions, key=lambda q: q.order_no)
        # O'quvchi javoblarini lug'atga joylash: (question_id, sub_part_label) -> AttemptAnswer
        ans_map = {}
        for a in att.answers:
            ans_map[(a.question_id, a.sub_part_label)] = a

        breakdown = []
        correct_count = 0
        wrong_count = 0
        unanswered_count = 0

        for q in questions:
            is_open = q.type in ("O", "O-1") or (q.type and q.type.startswith("O")) or bool(q.sub_parts and len(q.sub_parts) > 0) or q.order_no >= 36
            if is_open:
                # Ochiq savol (a va b qismlar)
                sub_parts = q.sub_parts or [{"label": "a", "correct_answer": ""}, {"label": "b", "correct_answer": ""}]
                parts_data = []
                q_all_correct = True
                q_has_any_answer = False

                for sp in sub_parts:
                    label = sp.get("label", "a")
                    corr_val = str(sp.get("correct_answer", "")).strip()
                    ans_obj = ans_map.get((q.id, label))
                    user_val = ans_obj.user_answer.strip() if ans_obj else ""
                    is_corr = ans_obj.is_correct if ans_obj else False

                    if user_val:
                        q_has_any_answer = True
                    if is_corr:
                        correct_count += 1
                    else:
                        q_all_correct = False
                        if user_val:
                            wrong_count += 1
                        else:
                            unanswered_count += 1

                    parts_data.append({
                        "label": label,
                        "user_answer": user_val or None,
                        "correct_answer": corr_val,
                        "is_correct": is_corr,
                        "status": "correct" if is_corr else ("wrong" if user_val else "unanswered"),
                    })

                breakdown.append({
                    "question_id": q.id,
                    "order_no": q.order_no,
                    "type": "O",
                    "text": q.text,
                    "image_url": q.image_url,
                    "sub_parts": parts_data,
                    "is_correct": q_all_correct,
                    "status": "correct" if q_all_correct else ("partially_correct" if any(p["is_correct"] for p in parts_data) else ("wrong" if q_has_any_answer else "unanswered")),
                })
            else:
                # Y-1 yoki GROUPED savol
                ans_obj = ans_map.get((q.id, None))
                user_val = ans_obj.user_answer.strip() if ans_obj else ""
                corr_val = str(q.correct_answer or "").strip()
                is_corr = ans_obj.is_correct if ans_obj else False

                if not user_val:
                    status = "unanswered"
                    unanswered_count += 1
                elif is_corr:
                    status = "correct"
                    correct_count += 1
                else:
                    status = "wrong"
                    wrong_count += 1

                breakdown.append({
                    "question_id": q.id,
                    "order_no": q.order_no,
                    "type": q.type,
                    "text": q.text,
                    "image_url": q.image_url,
                    "options": q.options,
                    "user_answer": user_val or None,
                    "correct_answer": corr_val,
                    "is_correct": is_corr,
                    "status": status,
                })

        u = att.user
        return {
            "attempt_id": att.id,
            "test_id": att.test.id,
            "test_code": att.test.code,
            "test_title": att.test.title,
            "user_id": u.id if u else None,
            "telegram_id": u.telegram_id if u else None,
            "full_name": u.full_name if u else "Noma'lum",
            "phone_number": u.phone_number if u else None,
            "username": u.username if u else None,
            "raw_score": att.raw_score,
            "final_score": att.final_score,
            "grade": att.grade,
            "is_certified": att.is_certified,
            "finished_at": att.finished_at.strftime("%d.%m.%Y %H:%M") if att.finished_at else "",
            "total_items": len(breakdown),
            "correct_count": correct_count,
            "wrong_count": wrong_count,
            "unanswered_count": unanswered_count,
            "breakdown": breakdown,
        }


async def delete_attempt_by_id(attempt_id: int, admin_user_id: int) -> Tuple[bool, str, Optional[int]]:
    """Talabgorning urinish natijasini o'chirish"""
    async with async_session_maker() as session:
        user_stmt = select(User).where(User.id == admin_user_id)
        admin_user = (await session.execute(user_stmt)).scalar_one_or_none()

        att_stmt = (
            select(Attempt)
            .options(selectinload(Attempt.test))
            .where(Attempt.id == attempt_id)
        )
        att = (await session.execute(att_stmt)).scalar_one_or_none()
        if not att or not att.test:
            return False, "Natija topilmadi", None

        # Ruxsat tekshiruvi: faqat test egasi yoki super admin
        is_super = admin_user and (admin_user.role == "super_admin" or is_super_admin(admin_user.telegram_id))
        if admin_user and not is_super and att.test.created_by_user_id != admin_user_id:
            return False, "Ushbu natijani o'chirishga ruxsatingiz yo'q", None

        test_id = att.test.id

        # Sertifikat rasmi mavjud bo'lsa o'chirish
        try:
            cert_path = Path(f"uploads/certificates/cert_{attempt_id}.jpg")
            if cert_path.exists():
                cert_path.unlink()
        except Exception as e:
            logger.warning(f"Sertifikat faylini o'chirishda xatolik ({attempt_id}): {e}")

        await session.delete(att)
        await session.commit()
        return True, "Natija muvaffaqiyatli o'chirildi", test_id

