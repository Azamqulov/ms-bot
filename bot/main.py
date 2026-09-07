import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.config import settings
from bot.database.session import init_db
from bot.database.seed_data import seed_database
from bot.services.admin_service import ensure_super_admin
from bot.handlers import (
    common_router,
    admin_router,
    test_runner_router,
    open_question_router,
    history_router,
)

# Windows terminalida emoji chiqishini xavfsiz qilish
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("🚀 Milliy Sertifikat (Matematika) Bot ishga tushirilmoqda...")

    # 1. Ma'lumotlar bazasini initsializatsiya qilish
    logger.info("📦 Ma'lumotlar bazasi jadvallari yaratilmoqda...")
    await init_db()

    # 2. Boshlang'ich 45 talik mock testni bazaga yuklash (agar yo'q bo'lsa)
    logger.info("📝 Standart mock test savollari tekshirilmoqda...")
    test_obj = await seed_database()
    logger.info(f"✅ Test tayyor: '{test_obj.title}' (ID: {test_obj.id}, Savollar: {test_obj.question_count} ta)")

    # 3. Super adminni tasdiqlash
    await ensure_super_admin()
    logger.info(f"👑 Super Admin ID: {settings.SUPER_ADMIN_ID} faollashtirildi.")

    # 3. Aiogram Bot va Dispatcher sozlash
    if not settings.BOT_TOKEN or "TEST_BOT_TOKEN" in settings.BOT_TOKEN:
        logger.warning(
            "⚠️ DIQQAT: .env faylida haqiqiy BOT_TOKEN kiritilmagan. "
            "Botni real Telegram tarmog'ida ishga tushirish uchun .env faylidagi BOT_TOKEN ni o'zgartiring!"
        )

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # 4. Routerlarni ro'yxatdan o'tkazish
    dp.include_router(common_router)
    dp.include_router(admin_router)
    dp.include_router(test_runner_router)
    dp.include_router(open_question_router)
    dp.include_router(history_router)

    # 5. FastAPI Web server va Telegram botni bir vaqtda ishga tushirish
    import uvicorn
    from bot.web_app.api import app as fastapi_app

    web_config = uvicorn.Config(
        app=fastapi_app,
        host=settings.WEB_SERVER_HOST,
        port=settings.WEB_SERVER_PORT,
        log_level="warning",
    )
    server = uvicorn.Server(web_config)

    logger.info(f"🌐 Web Server http://{settings.WEB_SERVER_HOST}:{settings.WEB_SERVER_PORT} manzilida ishga tushdi.")
    logger.info("🤖 Bot polling rejimida xabarlarni qabul qilishga tayyor.")

    try:
        await asyncio.gather(
            dp.start_polling(bot),
            server.serve(),
        )
    finally:
        await bot.session.close()
        logger.info("🛑 Bot to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot jarayoni to'xtatildi.")
