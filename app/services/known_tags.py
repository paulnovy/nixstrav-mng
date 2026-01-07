from __future__ import annotations

import fcntl
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from sqlalchemy.orm import Session

from ..models import Tag
from .epc import normalize_epc


def read_known_tags_safe(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    lock_path = Path(str(path) + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a+") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_SH)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def write_known_tags_atomic(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = Path(str(path) + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a+") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        fd, tmp_path = tempfile.mkstemp(
            dir=path.parent, prefix=path.name, suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(data, tmp_file, indent=2, ensure_ascii=False)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            os.replace(tmp_path, path)
            dir_fd = os.open(path.parent, os.O_DIRECTORY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def load_known_tags(path: Path) -> Dict[str, Any]:
    return read_known_tags_safe(path)


def atomic_write_known_tags(path: Path, data: Dict[str, Any]) -> None:
    write_known_tags_atomic(path, data)


def sync_json_to_db(session: Session, path: Path) -> None:
    """
    Seed DB with contents of known_tags.json if DB empty.
    """
    if session.query(Tag).count() > 0:
        return
    data = read_known_tags_safe(path)
    if not isinstance(data, dict):
        return
    for epc, meta in data.items():
        canonical = normalize_epc(epc)
        if not canonical:
            continue
        meta = meta or {}
        if not isinstance(meta, dict):
            meta = {}
        alias = meta.get("alias") or meta.get("owner") or canonical
        tag = Tag(
            epc=canonical,
            alias=alias,
            alias_group=meta.get("alias_group"),
            room_number=meta.get("room_number"),
            notes=meta.get("notes") or meta.get("note"),
            status=meta.get("status", "active"),
        )
        session.merge(tag)
    session.commit()


def persist_db_to_json(session: Session, path: Path) -> None:
    """
    Persist tags table to known_tags.json using atomic write.
    """
    tags = session.query(Tag).all()
    payload: Dict[str, Any] = {}
    for tag in tags:
        payload[tag.epc] = {
            "alias": tag.alias,
            "alias_group": tag.alias_group,
            "room_number": tag.room_number,
            "notes": tag.notes,
            "status": tag.status,
        }
    write_known_tags_atomic(path, payload)
