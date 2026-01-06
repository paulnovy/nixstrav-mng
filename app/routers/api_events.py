import csv
import io
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import User
from ..security import require_user
from ..services.events import (
    EventFilters,
    events_per_day,
    events_per_hour,
    export_events,
    list_events,
    top_readers,
    top_reasons,
    unknown_tags,
)

router = APIRouter()


async def _current_viewer(request: Request, db: Session = Depends(get_db)) -> User:
    return await require_user(request, db)


@router.get("")
async def get_events(
    request: Request,
    user: User = Depends(_current_viewer),
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None,
    reader_id: Optional[str] = None,
    reason: Optional[str] = None,
    tag: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    export: Optional[str] = None,
):
    filters = EventFilters(
        from_ts=from_ts,
        to_ts=to_ts,
        reader_id=reader_id,
        reason=reason,
        tag=tag,
        page=page,
        page_size=page_size,
    )
    events_db = str(request.app.state.events_db_path)
    if export:
        data = export_events(events_db, filters)
        if export == "csv":
            buf = io.StringIO()
            writer = csv.DictWriter(
                buf,
                fieldnames=[
                    "id",
                    "reader_id",
                    "tag",
                    "ts_client",
                    "received_at",
                    "source_ip",
                    "fired",
                    "reason",
                ],
            )
            writer.writeheader()
            writer.writerows(data)
            return Response(
                content=buf.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=events.csv"},
            )
        return data
    items, total = list_events(events_db, filters)
    return {"items": items, "total": total}


@router.get("/stats/overview")
async def stats_overview(request: Request, user: User = Depends(_current_viewer)):
    events_db = str(request.app.state.events_db_path)
    return {
        "events_per_day": events_per_day(events_db),
        "events_per_hour": events_per_hour(events_db),
        "top_reasons": top_reasons(events_db),
        "top_readers": top_readers(events_db),
    }


@router.get("/stats/unknown-tags")
async def stats_unknown_tags(request: Request, user: User = Depends(_current_viewer)):
    events_db = str(request.app.state.events_db_path)
    return unknown_tags(events_db)


@router.get("/stats/readers")
async def stats_readers(request: Request, user: User = Depends(_current_viewer)):
    events_db = str(request.app.state.events_db_path)
    return top_readers(events_db, limit=20)
