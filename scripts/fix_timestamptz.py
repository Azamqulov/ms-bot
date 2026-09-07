import sys
sys.path.insert(0, ".")
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from bot.config import settings

DATABASE_URL = os.getenv("SUPABASE_URL") or settings.DATABASE_URL

async def fix_columns():
    engine = create_async_engine(
        DATABASE_URL,
        connect_args={"statement_cache_size": 0}
    )
    commands = [
        "ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';",
        "ALTER TABLE tests ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';",
        "ALTER TABLE attempts ALTER COLUMN started_at TYPE TIMESTAMPTZ USING started_at AT TIME ZONE 'UTC';",
        "ALTER TABLE attempts ALTER COLUMN finished_at TYPE TIMESTAMPTZ USING finished_at AT TIME ZONE 'UTC';",
        "ALTER TABLE attempt_answers ALTER COLUMN answered_at TYPE TIMESTAMPTZ USING answered_at AT TIME ZONE 'UTC';"
    ]
    async with engine.begin() as conn:
        for cmd in commands:
            print(f"Executing: {cmd}")
            await conn.execute(text(cmd))
    print("All datetime columns converted to TIMESTAMPTZ successfully!")

if __name__ == "__main__":
    asyncio.run(fix_columns())
