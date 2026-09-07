import sys
import os
sys.path.insert(0, os.path.abspath("."))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text
from bot.database.models import Base, User, Test, Question, QuestionGroup, Attempt, AttemptAnswer

from bot.config import settings

SQLITE_URL = 'sqlite+aiosqlite:///./data/msbot.db'
SUPABASE_URL = os.getenv('SUPABASE_URL') or settings.DATABASE_URL

async def migrate():
    print('1. Connecting to SQLite and Supabase...')
    sqlite_eng = create_async_engine(SQLITE_URL)
    supa_eng = create_async_engine(
        SUPABASE_URL,
        connect_args={'statement_cache_size': 0},
        pool_pre_ping=True
    )

    print('2. Creating tables in Supabase...')
    async with supa_eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sqlite_session_maker = async_sessionmaker(sqlite_eng, class_=AsyncSession, expire_on_commit=False)
    supa_session_maker = async_sessionmaker(supa_eng, class_=AsyncSession, expire_on_commit=False)

    print('3. Migrating data from SQLite to Supabase...')
    async with sqlite_session_maker() as sq_s, supa_session_maker() as sp_s:
        # Users
        users = (await sq_s.execute(select(User))).scalars().all()
        for u in users:
            sp_u = User(
                id=u.id,
                telegram_id=u.telegram_id,
                full_name=u.full_name,
                username=u.username,
                phone_number=u.phone_number,
                role=u.role,
                created_at=u.created_at
            )
            await sp_s.merge(sp_u)
        await sp_s.commit()
        print(f'   Migrated {len(users)} users.')

        # Tests
        tests = (await sq_s.execute(select(Test))).scalars().all()
        valid_test_ids = set()
        for t in tests:
            sp_t = Test(
                id=t.id,
                created_by_user_id=t.created_by_user_id,
                code=t.code,
                title=t.title,
                description=t.description,
                time_limit_min=t.time_limit_min,
                question_count=t.question_count,
                is_active=t.is_active,
                created_at=t.created_at
            )
            await sp_s.merge(sp_t)
            valid_test_ids.add(t.id)
        await sp_s.commit()
        print(f'   Migrated {len(tests)} tests.')

        # Question Groups
        groups = (await sq_s.execute(select(QuestionGroup))).scalars().all()
        valid_group_ids = set()
        migrated_groups = 0
        for g in groups:
            if g.test_id not in valid_test_ids:
                continue
            sp_g = QuestionGroup(
                id=g.id,
                test_id=g.test_id,
                shared_context_text=g.shared_context_text,
                shared_image_url=g.shared_image_url,
                shared_options=g.shared_options
            )
            await sp_s.merge(sp_g)
            valid_group_ids.add(g.id)
            migrated_groups += 1
        await sp_s.commit()
        print(f'   Migrated {migrated_groups} question groups.')

        # Questions
        questions = (await sq_s.execute(select(Question))).scalars().all()
        valid_question_ids = set()
        migrated_questions = 0
        for q in questions:
            if q.test_id not in valid_test_ids:
                continue
            sp_q = Question(
                id=q.id,
                test_id=q.test_id,
                group_id=q.group_id if q.group_id in valid_group_ids else None,
                order_no=q.order_no,
                type=q.type,
                section=q.section,
                difficulty_b=q.difficulty_b,
                text=q.text,
                image_url=q.image_url,
                options=q.options,
                correct_answer=q.correct_answer,
                sub_parts=q.sub_parts
            )
            await sp_s.merge(sp_q)
            valid_question_ids.add(q.id)
            migrated_questions += 1
        await sp_s.commit()
        print(f'   Migrated {migrated_questions} questions.')

        # Attempts
        attempts = (await sq_s.execute(select(Attempt))).scalars().all()
        valid_attempt_ids = set()
        migrated_attempts = 0
        for a in attempts:
            if a.test_id not in valid_test_ids:
                continue
            sp_a = Attempt(
                id=a.id,
                user_id=a.user_id,
                test_id=a.test_id,
                started_at=a.started_at,
                finished_at=a.finished_at,
                raw_score=a.raw_score,
                theta=a.theta,
                standard_error=a.standard_error,
                final_score=a.final_score,
                grade=a.grade,
                is_certified=a.is_certified,
                status=a.status
            )
            await sp_s.merge(sp_a)
            valid_attempt_ids.add(a.id)
            migrated_attempts += 1
        await sp_s.commit()
        print(f'   Migrated {migrated_attempts} attempts.')

        # Attempt Answers
        answers = (await sq_s.execute(select(AttemptAnswer))).scalars().all()
        migrated_answers = 0
        for ans in answers:
            if ans.attempt_id not in valid_attempt_ids or ans.question_id not in valid_question_ids:
                continue
            sp_ans = AttemptAnswer(
                id=ans.id,
                attempt_id=ans.attempt_id,
                question_id=ans.question_id,
                sub_part_label=ans.sub_part_label,
                user_answer=ans.user_answer,
                is_correct=ans.is_correct,
                answered_at=ans.answered_at
            )
            await sp_s.merge(sp_ans)
            migrated_answers += 1
        await sp_s.commit()
        print(f'   Migrated {migrated_answers} attempt answers.')

    # Sync Postgres Primary Key Sequences
    async with supa_eng.begin() as conn:
        for tbl in ['users', 'tests', 'questions', 'question_groups', 'attempts', 'attempt_answers']:
            try:
                seq_sql = f"SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), coalesce(max(id), 1)) FROM {tbl}"
                await conn.execute(text(seq_sql))
            except Exception as e:
                print(f'Seq sync warning on {tbl}: {e}')

    print('SUCCESS: Full database migrated to Supabase!')

if __name__ == '__main__':
    asyncio.run(migrate())
