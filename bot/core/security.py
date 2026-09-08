"""
Xavfsizlik va Kriptografik Tokenlar moduli.
HMAC-SHA256 yordamida imzolangan talaba sessiya tokenlari va anti-spoofing himoyasi.
"""

import hmac
import hashlib
import base64
import json
import time
from typing import Optional, Dict, Any, Tuple
from bot.config import settings


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_student_session_token(
    telegram_id: int,
    test_id: int,
    secret_key: Optional[str] = None,
    expires_in_seconds: int = 18000,  # 5 soat (test muddati + zaxira)
) -> str:
    """
    Talabaning test topshirish sessiyasi uchun HMAC-SHA256 bilan imzolangan token yaratadi.
    """
    key = (secret_key or settings.BOT_TOKEN).encode("utf-8")
    now = int(time.time())
    payload = {
        "tg_id": telegram_id,
        "test_id": test_id,
        "iat": now,
        "exp": now + expires_in_seconds,
    }

    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64_encode(payload_json)

    signature = hmac.new(key, payload_b64.encode("utf-8"), hashlib.sha256).digest()
    sig_b64 = _b64_encode(signature)

    return f"{payload_b64}.{sig_b64}"


def verify_student_session_token(
    token: str,
    secret_key: Optional[str] = None,
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Talaba sessiya tokenini tekshiradi.
    Qaytaradi: (yaroqlimi, payload, xatolik_matni)
    """
    if not token or "." not in token:
        return False, None, "Token formati noto'g'ri."

    parts = token.split(".")
    if len(parts) != 2:
        return False, None, "Token bo'laklari yaroqsiz."

    payload_b64, sig_b64 = parts
    key = (secret_key or settings.BOT_TOKEN).encode("utf-8")

    # Imzoni tekshirish
    expected_sig = hmac.new(key, payload_b64.encode("utf-8"), hashlib.sha256).digest()
    expected_sig_b64 = _b64_encode(expected_sig)

    if not hmac.compare_digest(sig_b64, expected_sig_b64):
        return False, None, "Token imzosi noto'g'ri (soxtalashtirilgan)."

    try:
        payload_bytes = _b64_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        return False, None, "Token ma'lumotlarini o'qib bo'lmadi."

    # Muddat tekshiruvi
    exp = payload.get("exp", 0)
    if time.time() > exp:
        return False, payload, "Sessiya tokenining muddati tugagan."

    return True, payload, None
