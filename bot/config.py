from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Telegram Bot Token (@BotFather orqali olinadi).
    # DIQQAT: Ushbu token Telegram Mini App initData ma'lumotlarini serverda
    # HMAC-SHA256 orqali kriptografik tasdiqlash uchun ham qat'iy zarur!
    BOT_TOKEN: str = "123456789:TEST_BOT_TOKEN_CHANGE_ME"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/msbot.db"
    SUPER_ADMIN_ID: int = 1685356708
    ADMIN_IDS: str = "1685356708"
    DEFAULT_TEST_TIME_LIMIT_MIN: int = 150
    WEB_SERVER_HOST: str = "0.0.0.0"
    WEB_SERVER_PORT: int = 8000
    WEB_APP_URL: str = "https://azamqulov.github.io/ms-bot/"
    API_SERVER_URL: str = ""  # cloudflared yoki real server URL (masalan: https://xxxx.trycloudflare.com)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def admin_ids_list(self) -> List[int]:
        ids = [self.SUPER_ADMIN_ID]
        if self.ADMIN_IDS:
            for part in self.ADMIN_IDS.split(","):
                part = part.strip()
                if part.isdigit():
                    num = int(part)
                    if num not in ids:
                        ids.append(num)
        return ids


settings = Settings()
