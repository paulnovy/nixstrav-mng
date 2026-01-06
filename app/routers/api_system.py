import json
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SystemNode, SystemReader, User
from ..security import require_user
from ..services.system_status import check_service_status, problems, reader_status_heuristic

router = APIRouter()


async def _current_viewer(request: Request, db: Session = Depends(get_db)) -> User:
    return await require_user(request, db)


class HeartbeatReader(BaseModel):
    reader_id: str
    type: Optional[str] = None
    conn: Optional[str] = None
    last_read_at: Optional[datetime] = None
    meta: Optional[dict[str, Any]] = None


class HeartbeatPayload(BaseModel):
    node_id: str
    hostname: Optional[str] = None
    ip: Optional[str] = None
    uptime_sec: Optional[int] = None
    cpu: Optional[float] = None
    ram: Optional[float] = None
    disk: Optional[float] = None
    readers: List[HeartbeatReader] = []
    meta: Optional[dict[str, Any]] = None


@router.get("/services")
async def services_status(request: Request, user: User = Depends(_current_viewer)):
    services = [
        check_service_status("rfid-server.service"),
        check_service_status("nixstrav-mng.service"),
        check_service_status("cf601d.service"),
    ]
    return services


@router.get("/readers")
async def readers_status(request: Request, user: User = Depends(_current_viewer)):
    events_db = str(request.app.state.events_db_path)
    return reader_status_heuristic(events_db)


@router.get("/problems")
async def problems_view(request: Request, user: User = Depends(_current_viewer)):
    events_db = str(request.app.state.events_db_path)
    return problems(events_db)


@router.post("/heartbeat")
async def heartbeat(
    payload: HeartbeatPayload,
    request: Request,
    db: Session = Depends(get_db),
):
    node = db.get(SystemNode, payload.node_id) or SystemNode(node_id=payload.node_id)
    node.hostname = payload.hostname
    node.ip = payload.ip
    node.last_seen = datetime.utcnow()
    node.meta_json = json.dumps(payload.meta) if payload.meta else node.meta_json
    db.add(node)
    db.commit()

    for reader in payload.readers:
        r = db.get(SystemReader, reader.reader_id) or SystemReader(reader_id=reader.reader_id)
        r.node_id = payload.node_id
        r.type = reader.type or r.type
        r.conn = reader.conn or r.conn
        r.last_seen = datetime.utcnow()
        r.last_read_at = reader.last_read_at or r.last_read_at
        r.meta_json = json.dumps(reader.meta) if reader.meta else r.meta_json
        db.add(r)
    db.commit()
    return {"status": "ok"}
