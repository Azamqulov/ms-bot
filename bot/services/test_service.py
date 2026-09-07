from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from bot.database.session import async_session_maker
from bot.database.models import User, Test, Question, QuestionGroup, Attempt, AttemptAnswer
from bot.core.rasch import RaschItem, RaschResult, evaluate_attempt
from bot.core.validator import check_open_answer, normalize_text_answer


async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    """Foydalanuvchini faqat telegram_id bo'yicha olish"""
    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()


async def get_or_create_user(
    telegram_id: int,
    full_name: str,
    username: Optional[str] = None,
    phone_number: Optional[str] = None,
) -> User:
    """Foydalanuvchini bazadan topish yoki yangisini yaratish"""
    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=telegram_id,
                full_name=full_name,
                username=username,
                phone_number=phone_number,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            changed = False
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                changed = True
            if username and user.username != username:
                user.username = username
                changed = True
            if phone_number and user.phone_number != phone_number:
                user.phone_number = phone_number
                changed = True
            if changed:
                await session.commit()
                await session.refresh(user)

        return user


async def update_user_profile(
    telegram_id: int,
    full_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    username: Optional[str] = None,
) -> User:
    """Foydalanuvchi ism-familiyasi va telefon raqamini saqlash/yangilash"""
    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=telegram_id,
                full_name=full_name or "Talabgor",
                username=username,
                phone_number=phone_number,
            )
            session.add(user)
        else:
            if full_name:
                user.full_name = full_name
            if phone_number:
                user.phone_number = phone_number
            if username:
                user.username = username

        await session.commit()
        await session.refresh(user)
        return user


async def get_default_test() -> Optional[Test]:
    """Standart faol mock testni olish"""
    async with async_session_maker() as session:
        stmt = (
            select(Test)
            .options(selectinload(Test.questions).selectinload(Question.group))
            .where(Test.is_active == True)
            .order_by(Test.id)
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()


async def get_active_attempt(user_id: int) -> Optional[Attempt]:
    """Foydalanuvchining hozirda tugatilmagan (faol) urinishini olish"""
    async with async_session_maker() as session:
        stmt = (
            select(Attempt)
            .where(Attempt.user_id == user_id, Attempt.status == "in_progress")
            .order_by(desc(Attempt.started_at))
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()


async def start_new_attempt(user_id: int, test_id: int) -> Attempt:
    """Yangi test urinishini boshlash"""
    async with async_session_maker() as session:
        # Avvalgi ochiq qolib ketgan urinishlar bo'lsa ularni yakunlash
        stmt = select(Attempt).where(Attempt.user_id == user_id, Attempt.status == "in_progress")
        res = await session.execute(stmt)
        for old_attempt in res.scalars().all():
            old_attempt.status = "abandoned"
            old_attempt.finished_at = datetime.now(timezone.utc)

        new_attempt = Attempt(
            user_id=user_id,
            test_id=test_id,
            status="in_progress",
            started_at=datetime.now(timezone.utc),
        )
        session.add(new_attempt)
        await session.commit()
        await session.refresh(new_attempt)
        return new_attempt


async def get_question_by_order(test_id: int, order_no: int) -> Optional[Question]:
    """Tartib raqami bo'yicha savolni olish (guruhi bilan birga)"""
    async with async_session_maker() as session:
        stmt = (
            select(Question)
            .options(selectinload(Question.group))
            .where(Question.test_id == test_id, Question.order_no == order_no)
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()


async def get_user_answers_map(attempt_id: int) -> Dict[str, str]:
    """
    Attempt uchun kiritilgan javoblarni lug'at ko'rinishida olish:
    Kalit: f'{question_id}' yoki f'{question_id}_{sub_part}'
    """
    async with async_session_maker() as session:
        stmt = select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt_id)
        res = await session.execute(stmt)
        answers = res.scalars().all()

        ans_map = {}
        for a in answers:
            key = f"{a.question_id}_{a.sub_part_label}" if a.sub_part_label else str(a.question_id)
            ans_map[key] = a.user_answer
        return ans_map


async def save_answer(
    attempt_id: int,
    question_id: int,
    user_answer: str,
    is_correct: bool,
    sub_part_label: Optional[str] = None
) -> AttemptAnswer:
    """Savolga berilgan javobni saqlash yoki yangilash"""
    async with async_session_maker() as session:
        stmt = select(AttemptAnswer).where(
            AttemptAnswer.attempt_id == attempt_id,
            AttemptAnswer.question_id == question_id,
            AttemptAnswer.sub_part_label == sub_part_label,
        )
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            existing.user_answer = user_answer
            existing.is_correct = is_correct
            existing.answered_at = datetime.now(timezone.utc)
            record = existing
        else:
            record = AttemptAnswer(
                attempt_id=attempt_id,
                question_id=question_id,
                sub_part_label=sub_part_label,
                user_answer=user_answer,
                is_correct=is_correct,
                answered_at=datetime.now(timezone.utc),
            )
            session.add(record)

        await session.commit()
        await session.refresh(record)
        return record


async def finish_attempt(attempt_id: int) -> Tuple[Attempt, RaschResult]:
    """
    Testni to'liq yakunlash, RASH modeli bo'yicha baholash va natijalarni saqlash.
    """
    async with async_session_maker() as session:
        stmt = (
            select(Attempt)
            .options(selectinload(Attempt.test))
            .where(Attempt.id == attempt_id)
        )
        res = await session.execute(stmt)
        attempt = res.scalar_one_or_none()

        if not attempt:
            raise ValueError("Attempt topilmadi")

        # Testning barcha savollarini yuklash
        q_stmt = (
            select(Question)
            .where(Question.test_id == attempt.test_id)
            .order_by(Question.order_no)
        )
        q_res = await session.execute(q_stmt)
        questions = q_res.scalars().all()

        # Ushbu attempt uchun barcha berilgan javoblar
        ans_stmt = select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt_id)
        ans_res = await session.execute(ans_stmt)
        user_answers = ans_res.scalars().all()

        # Javoblarni tez qidirish uchun lug'at
        # Key: (question_id, sub_part_label) -> user_answer
        ans_dict = {
            (a.question_id, a.sub_part_label): a.user_answer
            for a in user_answers
        }

        # Rasch baholash uchun items va to'g'ri/xato bayroqlarini tayyorlash
        rasch_items: List[RaschItem] = []
        correct_flags: List[bool] = []

        for q in questions:
            if q.type in ("Y-1", "GROUPED"):
                # Bitta baholash bandi
                r_item = RaschItem(item_id=f"q_{q.id}", difficulty_b=q.difficulty_b)
                rasch_items.append(r_item)

                user_ans = ans_dict.get((q.id, None))
                is_correct = (user_ans == q.correct_answer) if user_ans else False
                correct_flags.append(is_correct)

                # Javobni bazada is_correct holatini ham mustahkamlash
                if user_ans:
                    for a in user_answers:
                        if a.question_id == q.id and a.sub_part_label is None:
                            a.is_correct = is_correct

            elif q.type == "O":
                # Ochiq savol - har bir sub_part (a, b) alohida Rasch item
                sub_parts = q.sub_parts or []
                for sp in sub_parts:
                    label = sp.get("label", "a")
                    diff_b = float(sp.get("difficulty_b", q.difficulty_b))
                    correct_val = sp.get("correct_answer", "")

                    r_item = RaschItem(item_id=f"q_{q.id}_{label}", difficulty_b=diff_b)
                    rasch_items.append(r_item)

                    user_ans = ans_dict.get((q.id, label))
                    is_correct = check_open_answer(user_ans or "", correct_val) if user_ans else False
                    correct_flags.append(is_correct)

                    # Javobni bazada is_correct yangilash
                    if user_ans:
                        for a in user_answers:
                            if a.question_id == q.id and a.sub_part_label == label:
                                a.is_correct = is_correct

        # RASH modeli orqali hisoblash
        rasch_result = evaluate_attempt(rasch_items, correct_flags)

        # Attempt jadvaliga yakuniy natijalarni saqlash
        attempt.status = "completed"
        attempt.finished_at = datetime.now(timezone.utc)
        attempt.raw_score = rasch_result.raw_score
        attempt.theta = rasch_result.theta
        attempt.standard_error = rasch_result.standard_error
        attempt.final_score = rasch_result.final_score
        attempt.grade = rasch_result.grade
        attempt.is_certified = rasch_result.is_certified

        await session.commit()
        await session.refresh(attempt)

        return attempt, rasch_result


async def get_user_attempts_history(user_id: int) -> List[Attempt]:
    """Foydalanuvchining o'tgan barcha yakunlangan natijalari tarixi"""
    async with async_session_maker() as session:
        stmt = (
            select(Attempt)
            .options(selectinload(Attempt.test))
            .where(Attempt.user_id == user_id, Attempt.status == "completed")
            .order_by(desc(Attempt.finished_at))
        )
        res = await session.execute(stmt)
        return res.scalars().all()
