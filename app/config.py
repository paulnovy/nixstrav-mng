from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseModel):
    session_cookie: str = "nixstrav_mng_session"
    session_secure: bool = True
    session_samesite: Literal["lax", "strict", "none"] = "lax"
    csrf_cookie: str = "nixstrav_mng_csrf"
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_sec: int = 900
    account_lock_minutes: int = 10


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="")

    # Paths (override in production via ENV)
    mng_db: Path = Path("data/mng.db")
    nixstrav_events_db: Path = Path("data/events.db")
    nixstrav_known_tags_json: Path = Path("data/known_tags.json")
    nixstrav_config_json: Path = Path("data/config.json")

    # Security / sessions
    session_secret: str = "changeme-session-secret"
    security: SecuritySettings = SecuritySettings()

    # CF601
    cf601_mode: Literal["keyboard", "service", "webserial"] = "keyboard"
    cf601d_url: str = "http://127.0.0.1:8888"

    # Misc
    debug: bool = False

    # Dev toggles
    dev_insecure_cookies: bool = False
    timezone: str = "UTC"
    reader_warn_sec: int = 90
    reader_offline_sec: int = 300


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
