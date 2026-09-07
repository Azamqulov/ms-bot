import urllib.parse
from typing import Optional, Any
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from bot.config import settings


def get_main_menu_keyboard(is_admin_user: bool = False, user: Optional[Any] = None) -> ReplyKeyboardMarkup:
    """Asosiy menyu klaviaturasi (Telegram WebApp integratsiyasi bilan)"""
    web_url = settings.WEB_APP_URL
    if user and getattr(user, 'full_name', None):
        params = {
            "tg_id": str(getattr(user, "telegram_id", "")),
            "name": getattr(user, "full_name", ""),
            "phone": getattr(user, "phone_number", "") or ""
        }
        query_str = urllib.parse.urlencode(params)
        delimiter = "&" if "?" in web_url else "?"
        web_url = f"{web_url}{delimiter}{query_str}"

    if settings.API_SERVER_URL and "github.io" in settings.WEB_APP_URL:
        api_clean = settings.API_SERVER_URL.rstrip('/')
        delimiter = "&" if "?" in web_url else "?"
        web_url = f"{web_url}{delimiter}api={urllib.parse.quote(api_clean, safe=':/')}"

    kb = [
        [
            KeyboardButton(
                text="🚀 Javobni tekshirish",
                web_app=WebAppInfo(url=web_url)
            ),
            KeyboardButton(text="📊 Natijalarim"),
        ],
        [
            KeyboardButton(text="ℹ️ RASH modeli haqida"),
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
