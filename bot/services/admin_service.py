"""
Admin va Super Admin boshqaruv servisi hamda Test yuklash logikasi.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from bot.config import settings
from bot.database.session import async_session_maker
from bot.database.models import User, Test, Question, QuestionGroup, Attempt


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
        # Kod band emasligini tekshirish
        stmt = select(Test).where(Test.code == clean_code)
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
        )
        session.add(new_test)
        await session.flush()

        # Guruhlangan kontekst bo'lsa
        group_id = None
        if grouped_context:
            shared_text = grouped_context.get("shared_context_text", "")
            shared_opts = grouped_context.get("shared_options", {})
            if shared_text:
                q_group = QuestionGroup(
                    test_id=new_test.id,
                    shared_context_text=shared_text,
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

        await session.commit()
        await session.refresh(new_test)
        return True, f"Test muvaffaqiyatli yuklandi! Kod: {clean_code}", new_test


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


def get_sample_test_template() -> str:
    """Adminlar to'ldirishi uchun qulay JSON shablon namunasi"""
    template = {
        "code": "MOCK-1",
        "title": "Milliy Sertifikat Matematika Sinovi",
        "description": "45 ta savolli mock test",
        "time_limit_min": 150,
        "questions": [
            {
                "order_no": 1,
                "type": "Y-1",
                "section": "Algebra",
                "difficulty_b": -1.0,
                "text": "Hisoblang: 2.5 * 4 - 3",
                "options": {
                    "A": "7",
                    "B": "8",
                    "C": "6",
                    "D": "5"
                },
                "correct_answer": "A"
            },
            {
                "order_no": 2,
                "type": "O",
                "section": "Geometriya",
                "difficulty_b": 0.5,
                "text": "Uchburchak katetlari 3 va 4.\na) Gipotenuzani toping.\nb) Yuzini toping.",
                "sub_parts": [
                    {"label": "a", "correct_answer": "5", "difficulty_b": 0.3},
                    {"label": "b", "correct_answer": "6", "difficulty_b": 0.7}
                ]
            }
        ]
    }
    return json.dumps(template, indent=2, ensure_ascii=False)
