"""
Telegram Mini App initData autentifikatsiya va xavfsizlik moduli.
Telegram rasmiy spetsifikatsiyasi bo'yicha server tomonida ma'lumotlarni tekshirish:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl, urlencode
from typing import Optional, Dict, Any

from fastapi import Header, HTTPException, status

from bot.config import settings
from bot.services.admin_service import is_admin


def parse_and_verify_telegram_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = 86400,
) -> Dict[str, Any]:
    """
    Telegram Mini App initData satrini serverda kriptografik tekshiradi.

    1. 'hash' parametrini ajratadi.
    2. Qolgan parametrlarni kalitlari bo'yicha alfavit tartibida saralab,
       'key=value' formatida '\\n' bilan birlashtiradi.
    3. secret_key = HMAC_SHA256(b"WebAppData", bot_token.encode('utf-8'))
    4. calculated_hash = HMAC_SHA256(secret_key, data_check_string.encode('utf-8')).hexdigest()
    5. Hash mosligini tekshiradi (hmac.compare_digest).
    6. auth_date 24 soatdan eski emasligini tekshiradi.
    7. Foydalanuvchi ma'lumotlarini qaytaradi.
    """
    if not init_data or not isinstance(init_data, str) or not init_data.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentifikatsiya uchun 'X-Telegram-Init-Data' sarlavhasi talab qilinadi.",
        )

    try:
        parsed_pairs = parse_qsl(init_data, keep_blank_values=True)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="initData formati noto'g'ri.",
        )

    if not parsed_pairs:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="initData parametrlari bo'sh.",
        )

    parsed_dict = dict(parsed_pairs)
    received_hash = parsed_dict.get("hash")
    if not received_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="initData ichida 'hash' parametri topilmadi.",
        )

    # hash parametrini chiqarib tashlab, qolganlarini kalit bo'yicha alfavit tartibida saralash
    check_pairs = []
    for k, v in sorted(parsed_pairs):
        if k != "hash":
            check_pairs.append(f"{k}={v}")

    data_check_string = "\n".join(check_pairs)

    # HMAC-SHA256 hisoblash
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram autentifikatsiyasi xato (hash mos kelmadi).",
        )

    # auth_date tekshiruvi (24 soatlik muddat)
    auth_date_str = parsed_dict.get("auth_date")
    if not auth_date_str or not auth_date_str.isdigit():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="initData ichida 'auth_date' topilmadi yoki noto'g'ri.",
        )

    auth_date = int(auth_date_str)
    current_time = int(time.time())
    if current_time - auth_date > max_age_seconds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram sessiyasi eskirgan (24 soatdan ortiq vaqt o'tgan).",
        )

    # Kelajakdagi soxta auth_date lar uchun himoya (60 sekundlik ruxsat etilgan farq bilan)
    if auth_date - current_time > 60:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="auth_date vaqti noto'g'ri (kelajakdagi vaqt).",
        )

    # Foydalanuvchi ma'lumotlarini ajratib olish
    user_raw = parsed_dict.get("user")
    if not user_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="initData ichida 'user' ma'lumotlari mavjud emas.",
        )

    try:
        user_data = json.loads(user_raw)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="initData ichidagi 'user' ma'lumotlari JSON formatida emas.",
        )

    return {
        "user": user_data,
        "auth_date": auth_date,
        "query_id": parsed_dict.get("query_id"),
        "raw": parsed_dict,
    }


async def require_admin_user(
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
) -> int:
    """
    FastAPI Dependency:
    Admin API endpointlarini himoya qilish uchun.
    Faqat haqiqiy Telegram initData bilan tasdiqlangan va admin huquqiga
    ega foydalanuvchilarning telegram_id sini qaytaradi.
    """
    if not x_telegram_init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentifikatsiya uchun 'X-Telegram-Init-Data' HTTP sarlavhasi talab qilinadi.",
        )

    verified = parse_and_verify_telegram_init_data(
        init_data=x_telegram_init_data,
        bot_token=settings.BOT_TOKEN,
    )
    user_info = verified.get("user") or {}
    telegram_id = user_info.get("id")

    if not telegram_id or not isinstance(telegram_id, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Foydalanuvchi Telegram ID si aniqlanmadi.",
        )

    is_adm = await is_admin(telegram_id)
    if not is_adm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ushbu amalni bajarish uchun administratorlik huquqi talab qilinadi.",
        )

    return telegram_id


def create_mock_init_data(
    user_id: int,
    bot_token: Optional[str] = None,
    auth_date: Optional[int] = None,
    is_valid: bool = True,
    username: str = "test_admin",
    first_name: str = "Admin",
) -> str:
    """
    Testlar va avtomatlashtirish uchun yaroqli yoki soxta Telegram initData hosil qiladi.
    """
    token = bot_token or settings.BOT_TOKEN
    if auth_date is None:
        auth_date = int(time.time())

    user_obj = {
        "id": user_id,
        "first_name": first_name,
        "username": username,
    }
    user_str = json.dumps(user_obj, separators=(",", ":"))

    data = {
        "auth_date": str(auth_date),
        "query_id": "AAHdF6IQAAAAAN0XohD_test",
        "user": user_str,
    }

    items = sorted(data.items())
    data_check_string = "\n".join(f"{k}={v}" for k, v in items)

    secret_key = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
    valid_hash = hmac.new(
        secret_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    data["hash"] = valid_hash if is_valid else "invalid_hash_value_1234567890abcdef"
    return urlencode(data)
