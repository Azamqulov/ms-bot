from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from bot.config import settings


def get_main_menu_keyboard(is_admin_user: bool = False) -> ReplyKeyboardMarkup:
    """Asosiy menyu klaviaturasi (Telegram WebApp integratsiyasi bilan)"""
    kb = [
        [
            KeyboardButton(
                text="🚀 Test topshirish (Web App)",
                web_app=WebAppInfo(url=settings.WEB_APP_URL)
            ),
            KeyboardButton(text="📊 Natijalarim"),
        ],
        [
            KeyboardButton(text="📝 Botda topshirish"),
            KeyboardButton(text="ℹ️ RASH modeli haqida"),
        ],
        [
            KeyboardButton(text="❓ Yordam"),
        ],
    ]
    if is_admin_user:
        kb.append([KeyboardButton(text="👑 Admin Panel")])

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Ochiq javob kiritishni bekor qilish tugmasi"""
    kb = [
        [KeyboardButton(text="❌ Bekor qilish / Orqaga")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_phone_request_keyboard() -> ReplyKeyboardMarkup:
    """Telefon raqamini ulashish tugmasi"""
    kb = [
        [KeyboardButton(text="📱 Telefon raqamimni yuborish", request_contact=True)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
