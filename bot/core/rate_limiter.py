"""
In-Memory Sliding Window Rate Limiter moduli.
FastAPI so'rovlarini DDoS, scraping va brute-force spamlaridan himoyalash uchun.
"""

import time
import asyncio
from typing import Dict, List, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """
    Sliding window algoritmi bo'yicha mijoz so'rovlarini hisoblovchi va cheklovchi xizmat.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Kalit -> [timestamp1, timestamp2, ...]
        self._records: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self, client_key: str) -> tuple[bool, int]:
        """
        Mijozga ruxsat berilganligini tekshiradi.
        Qaytaradi: (ruxsat_berildimi: bool, qolgan_kutish_sekundi: int)
        """
        now = time.time()
        window_start = now - self.window_seconds

        async with self._lock:
            timestamps = self._records.get(client_key, [])
            # Oynadan tashqaridagi eski vaqtlarni tozalash
            valid_timestamps = [t for t in timestamps if t > window_start]

            if len(valid_timestamps) >= self.max_requests:
                # Eng eski so'rov o'tguncha qolgan vaqt
                oldest = valid_timestamps[0]
                retry_after = int(self.window_seconds - (now - oldest)) + 1
                self._records[client_key] = valid_timestamps
                return False, max(1, retry_after)

            valid_timestamps.append(now)
            self._records[client_key] = valid_timestamps
            return True, 0

    async def cleanup(self):
        """Xotirani tozalash (vaqti-vaqti bilan eski kalitlarni to'liq o'chirish)"""
        now = time.time()
        window_start = now - self.window_seconds
        async with self._lock:
            keys_to_del = [k for k, v in self._records.items() if not v or v[-1] < window_start]
            for k in keys_to_del:
                del self._records[k]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI HTTP Middleware: Barcha kiruvchi so'rovlarni mijoz IP'si bo'yicha tekshiradi.
    Statik fayllar (/uploads, /static, /css, /js, /favicon.ico) uchun limit qo'llanilmaydi.
    """

    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.limiter = SlidingWindowRateLimiter(max_requests=max_requests, window_seconds=window_seconds)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Statik fayllar va sog'lik tekshiruvini cheklovdan chiqarish
        if (
            path.startswith("/uploads")
            or path.startswith("/static")
            or path.startswith("/css")
            or path.startswith("/js")
            or path == "/healthz"
            or path.endswith(".ico")
        ):
            return await call_next(request)

        # Mijoz IP manzilini aniqlash (Reverse proxy yoki Cloudflare bo'lsa CF-Connecting-IP / X-Forwarded-For)
        client_ip = (
            request.headers.get("CF-Connecting-IP")
            or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )

        allowed, retry_after = await self.limiter.is_allowed(client_ip)
        if not allowed:
            logger.warning(f"🚨 Rate limit oshirildi: IP {client_ip}, path: {path}")
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"So'rovlar soni me'yordan oshdi. Iltimos, {retry_after} soniyadan so'ng qayta urining.",
                        "retry_after": retry_after,
                    },
                },
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)
        return response
