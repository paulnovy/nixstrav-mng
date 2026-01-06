import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    operator = "operator"
    viewer = "viewer"

    @classmethod
    def as_choices(cls) -> list[str]:
        return [r.value for r in cls]

    def rank(self) -> int:
        order = {
            UserRole.admin: 3,
            UserRole.operator: 2,
            UserRole.viewer: 1,
        }
        return order[self]


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default=UserRole.viewer.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user_obj", cascade="all,delete")


class Tag(Base):
    __tablename__ = "tags"

    epc: Mapped[str] = mapped_column(String(64), primary_key=True)
    alias: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    alias_group: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    room_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    user: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    before_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    after_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))

    user_obj: Mapped[Optional[User]] = relationship("User", back_populates="audit_logs")


class SystemNode(Base):
    __tablename__ = "system_nodes"

    node_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    hostname: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    meta_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    readers: Mapped[list["SystemReader"]] = relationship(
        "SystemReader", back_populates="node", cascade="all,delete-orphan"
    )


class SystemReader(Base):
    __tablename__ = "system_readers"

    reader_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    node_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("system_nodes.node_id"), nullable=True
    )
    type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    conn: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    meta_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    node: Mapped[Optional[SystemNode]] = relationship("SystemNode", back_populates="readers")
