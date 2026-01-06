from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import User, UserRole
from ..security import get_password_hash, verify_password


def get_user_by_username(session: Session, username: str) -> Optional[User]:
    stmt = select(User).where(User.username == username)
    return session.scalars(stmt).first()


def authenticate_user(session: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(session, username)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login_at = datetime.utcnow()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_user(
    session: Session, username: str, password: str, role: UserRole = UserRole.viewer
) -> User:
    user = User(
        username=username,
        password_hash=get_password_hash(password),
        role=role.value,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def ensure_admin_exists(session: Session, username: str = "admin", password: str = "admin") -> None:
    if session.query(User).count() == 0:
        create_user(session, username=username, password=password, role=UserRole.admin)
