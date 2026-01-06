import secrets
import time
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User, UserRole


pwd_context = CryptContext(schemes=["argon2", "bcrypt_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


class LoginRateLimiter:
    """
    In-memory login rate limiter keyed by username+ip.
    """

    def __init__(self, attempts: int, window_sec: int, lock_minutes: int) -> None:
        self.attempts = attempts
        self.window_sec = window_sec
        self.lock_minutes = lock_minutes
        self.failures: dict[str, list[float]] = {}
        self.locked_until: dict[str, float] = {}

    def _key(self, username: str, ip: str) -> str:
        return f"{username}:{ip}"

    def is_locked(self, username: str, ip: str) -> bool:
        key = self._key(username, ip)
        until = self.locked_until.get(key)
        if until and until > time.time():
            return True
        if until and until <= time.time():
            self.locked_until.pop(key, None)
        return False

    def register_failure(self, username: str, ip: str) -> None:
        key = self._key(username, ip)
        now = time.time()
        window_start = now - self.window_sec
        recent = [ts for ts in self.failures.get(key, []) if ts >= window_start]
        recent.append(now)
        self.failures[key] = recent
        if len(recent) >= self.attempts:
            self.locked_until[key] = now + self.lock_minutes * 60

    def register_success(self, username: str, ip: str) -> None:
        key = self._key(username, ip)
        self.failures.pop(key, None)
        self.locked_until.pop(key, None)


login_limiter = LoginRateLimiter(
    attempts=settings.security.login_rate_limit_attempts,
    window_sec=settings.security.login_rate_limit_window_sec,
    lock_minutes=settings.security.account_lock_minutes,
)


def get_session_user(request: Request, db: Session) -> Optional[User]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, int(user_id))


async def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_session_user(request, db)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


def ensure_role(user: User, minimum: UserRole) -> None:
    if UserRole(user.role).rank() < minimum.rank():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


async def require_role(
    request: Request, minimum: UserRole, db: Session = Depends(get_db)
) -> User:
    user = await require_user(request, db)
    ensure_role(user, minimum)
    return user


async def csrf_protect(request: Request) -> None:
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    token_in_session = request.session.get("csrf_token")
    token = request.headers.get("X-CSRF-Token")
    ctype = request.headers.get("content-type", "")
    if token is None and (
        "application/x-www-form-urlencoded" in ctype or "multipart/form-data" in ctype
    ):
        form = await request.form()
        token = form.get("csrf_token") if form else None
    if not token_in_session or not token or token_in_session != token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid",
        )


def get_or_create_csrf(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token
