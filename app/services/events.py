from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _connect(db_path: str) -> sqlite3.Connection:
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.OperationalError:
        conn = sqlite3.connect(":memory:")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                reader_id TEXT,
                tag TEXT,
                ts_client TEXT,
                received_at TEXT,
                source_ip TEXT,
                fired INTEGER,
                reason TEXT
            )
            """
        )
    conn.row_factory = sqlite3.Row
    return conn


@dataclass
class EventFilters:
    from_ts: Optional[str] = None
    to_ts: Optional[str] = None
    reader_id: Optional[str] = None
    reason: Optional[str] = None
    tag: Optional[str] = None
    page: int = 1
    page_size: int = 50


def list_events(db_path: str, filters: EventFilters) -> Tuple[List[Dict[str, Any]], int]:
    conds = []
    params: list[Any] = []
    if filters.from_ts:
        conds.append("received_at >= ?")
        params.append(filters.from_ts)
    if filters.to_ts:
        conds.append("received_at <= ?")
        params.append(filters.to_ts)
    if filters.reader_id:
        conds.append("reader_id = ?")
        params.append(filters.reader_id)
    if filters.reason:
        conds.append("reason = ?")
        params.append(filters.reason)
    if filters.tag:
        conds.append("tag = ?")
        params.append(filters.tag)
    where = f"WHERE {' AND '.join(conds)}" if conds else ""

    query_base = f"FROM events {where}"
    count_sql = f"SELECT COUNT(*) {query_base}"
    sql = (
        f"SELECT id, reader_id, tag, ts_client, received_at, source_ip, fired, reason "
        f"{query_base} "
        "ORDER BY received_at DESC LIMIT ? OFFSET ?"
    )
    page_size = max(1, min(filters.page_size, 200))
    offset = max(0, filters.page - 1) * page_size
    with _connect(db_path) as conn:
        total = conn.execute(count_sql, params).fetchone()[0]
        rows = conn.execute(sql, params + [page_size, offset]).fetchall()
    return [dict(r) for r in rows], int(total)


def export_events(db_path: str, filters: EventFilters) -> List[Dict[str, Any]]:
    """
    Export all events matching filters (no pagination).
    """
    conds = []
    params: list[Any] = []
    if filters.from_ts:
        conds.append("received_at >= ?")
        params.append(filters.from_ts)
    if filters.to_ts:
        conds.append("received_at <= ?")
        params.append(filters.to_ts)
    if filters.reader_id:
        conds.append("reader_id = ?")
        params.append(filters.reader_id)
    if filters.reason:
        conds.append("reason = ?")
        params.append(filters.reason)
    if filters.tag:
        conds.append("tag = ?")
        params.append(filters.tag)
    where = f"WHERE {' AND '.join(conds)}" if conds else ""
    sql = (
        "SELECT id, reader_id, tag, ts_client, received_at, source_ip, fired, reason "
        f"FROM events {where} ORDER BY received_at DESC"
    )
    with _connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def events_per_day(db_path: str, days: int = 14) -> List[Dict[str, Any]]:
    sql = """
        SELECT date(received_at) AS day, COUNT(*) AS count
        FROM events
        GROUP BY day
        ORDER BY day DESC
        LIMIT ?
    """
    with _connect(db_path) as conn:
        rows = conn.execute(sql, (days,)).fetchall()
    return [dict(r) for r in rows]


def events_per_hour(db_path: str, days: int = 7) -> List[Dict[str, Any]]:
    sql = """
        SELECT strftime('%H', received_at) AS hour, COUNT(*) AS count
        FROM events
        WHERE received_at >= datetime('now', ?)
        GROUP BY hour
        ORDER BY hour
    """
    with _connect(db_path) as conn:
        rows = conn.execute(sql, (f"-{days} days",)).fetchall()
    return [dict(r) for r in rows]


def top_reasons(db_path: str, limit: int = 5) -> List[Dict[str, Any]]:
    sql = """
        SELECT reason, COUNT(*) AS count
        FROM events
        GROUP BY reason
        ORDER BY count DESC
        LIMIT ?
    """
    with _connect(db_path) as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(r) for r in rows]


def top_readers(db_path: str, limit: int = 5) -> List[Dict[str, Any]]:
    sql = """
        SELECT reader_id, COUNT(*) AS count
        FROM events
        GROUP BY reader_id
        ORDER BY count DESC
        LIMIT ?
    """
    with _connect(db_path) as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(r) for r in rows]


def unknown_tags(db_path: str, limit: int = 20) -> List[Dict[str, Any]]:
    sql = """
        SELECT tag, COUNT(*) AS count, MAX(received_at) AS last_seen
        FROM events
        WHERE reason = 'unknown_tag'
        GROUP BY tag
        ORDER BY last_seen DESC
        LIMIT ?
    """
    with _connect(db_path) as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(r) for r in rows]


def last_events_per_reader(db_path: str) -> List[Dict[str, Any]]:
    sql = """
        SELECT reader_id,
               MAX(received_at) AS last_event,
               SUM(CASE WHEN fired = 1 THEN 1 ELSE 0 END) AS fired_count,
               COUNT(*) AS total
        FROM events
        GROUP BY reader_id
    """
    with _connect(db_path) as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


def latest_events(db_path: str, limit: int = 20) -> List[Dict[str, Any]]:
    sql = """
        SELECT id, reader_id, tag, received_at, reason, fired
        FROM events
        ORDER BY received_at DESC
        LIMIT ?
    """
    with _connect(db_path) as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(r) for r in rows]


def events_for_tag(db_path: str, tag: str, limit: int = 20) -> List[Dict[str, Any]]:
    sql = """
        SELECT id, reader_id, tag, received_at, reason, fired
        FROM events
        WHERE tag = ?
        ORDER BY received_at DESC
        LIMIT ?
    """
    with _connect(db_path) as conn:
        rows = conn.execute(sql, (tag, limit)).fetchall()
    return [dict(r) for r in rows]


def events_for_reader(db_path: str, reader_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    sql = """
        SELECT id, reader_id, tag, received_at, reason, fired
        FROM events
        WHERE reader_id = ?
        ORDER BY received_at DESC
        LIMIT ?
    """
    with _connect(db_path) as conn:
        rows = conn.execute(sql, (reader_id, limit)).fetchall()
    return [dict(r) for r in rows]


def last_seen_for_tags(db_path: str, tags: List[str]) -> Dict[str, str]:
    if not tags:
        return {}
    placeholders = ",".join("?" for _ in tags)
    sql = (
        f"SELECT tag, MAX(received_at) AS last_seen FROM events "
        f"WHERE tag IN ({placeholders}) GROUP BY tag"
    )
    with _connect(db_path) as conn:
        rows = conn.execute(sql, tags).fetchall()
    return {r["tag"]: r["last_seen"] for r in rows if r["last_seen"]}


def recent_errors(db_path: str, limit: int = 10) -> List[Dict[str, Any]]:
    sql = """
        SELECT id, reader_id, tag, received_at, reason
        FROM events
        WHERE reason IN ('relay_error', 'unknown_tag')
        ORDER BY received_at DESC
        LIMIT ?
    """
    with _connect(db_path) as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(r) for r in rows]
