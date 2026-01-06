from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import User, UserRole
from ..security import get_or_create_csrf, login_limiter
from ..services import audit
from ..services.users import authenticate_user, get_user_by_username

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    username: str
    role: str
    is_active: bool
    last_login_at: Optional[datetime]


def _session_login(request: Request, user: User) -> None:
    request.session.clear()
    request.session["user_id"] = user.id
    request.session["role"] = user.role
    request.session["csrf_token"] = get_or_create_csrf(request)


@router.post("/login", response_model=UserResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    username = payload.username.strip()
    if login_limiter.is_locked(username, ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account locked due to failed attempts. Try later.",
        )
    user = authenticate_user(db, username, payload.password)
    if not user:
        login_limiter.register_failure(username, ip)
        audit.log_action(db, user=None, action="login_failed", entity_id=username, ip=ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    login_limiter.register_success(username, ip)
    _session_login(request, user)
    audit.log_action(db, user, action="login", entity_id=user.username, ip=ip)
    return UserResponse(
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
    )


@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    user: Optional[User] = None
    if request.session.get("user_id"):
        user = db.get(User, int(request.session["user_id"]))
    request.session.clear()
    if settings.security.session_secure:
        request.session["__deleted"] = True
    audit.log_action(db, user, action="logout", entity_id=user.username if user else None)
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
async def me(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return UserResponse(
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
    )
