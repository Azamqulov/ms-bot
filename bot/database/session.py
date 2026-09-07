import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from bot.config import settings
from bot.database.models import Base

import sys

# Agar pytest orqali ishga tushirilayotgan bo'lsa, ishlab turgan ma'lumotlar bazasiga
# ta'sir qilmaslik uchun avtomatik ravishda alohida test bazasi ishlatiladi
is_test_env = "pytest" in sys.modules or any("pytest" in arg.lower() for arg in sys.argv)
effective_db_url = "sqlite+aiosqlite:///./data/test_sandbox.db" if is_test_env else settings.DATABASE_URL

# Agar SQLite ishlatilsa va data papkasi yo'q bo'lsa, yaratamiz
if "sqlite" in effective_db_url:
    db_path = effective_db_url.replace("sqlite+aiosqlite:///", "")
    parent_dir = Path(db_path).parent
    if parent_dir and not parent_dir.exists():
        parent_dir.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    effective_db_url,
    echo=False,
    future=True
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db() -> None:
    """Ma'lumotlar bazasi jadvallarini initsializatsiya qilish"""
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # SQLite uchun yangi ustunlarni avtomatik qo'shish
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(32)"))
        except Exception:
            pass  # Ustun allaqachon mavjud bo'lsa xatoni e'tiborsiz qoldirish


async def get_session() -> AsyncSession:
    """Dependency yoki kontekst menejeri uchun sessiya olish"""
    async with async_session_maker() as session:
        yield session
