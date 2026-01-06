from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Tag, User, UserRole
from ..security import csrf_protect, require_user, require_role
from ..services import audit
from ..services.alias_generator import generate_alias
from ..services.events import last_seen_for_tags
from ..services.known_tags import persist_db_to_json

router = APIRouter()


class TagBase(BaseModel):
    alias: Optional[str] = None
    alias_group: Optional[str] = Field(None, description="male_tree/female_fruit")
    room_number: Optional[str] = None
    notes: Optional[str] = None
    status: str = "active"


class TagCreate(TagBase):
    epc: str


class TagUpdate(TagBase):
    pass


class TagResponse(TagBase):
    epc: str
    last_seen: Optional[str] = None

    class Config:
        orm_mode = True


async def _current_operator(
    request: Request, db: Session = Depends(get_db)
) -> User:
    return await require_role(request, UserRole.operator, db)


async def _current_viewer(request: Request, db: Session = Depends(get_db)) -> User:
    return await require_user(request, db)


@router.get("", response_model=List[TagResponse])
async def list_tags(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(_current_viewer),
):
    tags = db.scalars(select(Tag)).all()
    events_db = str(
        getattr(request.app.state, "events_db_path", None) or settings.nixstrav_events_db
    )
    last_seen_map = last_seen_for_tags(events_db, tags=[t.epc for t in tags])
    response = []
    for tag in tags:
        response.append(
            TagResponse(
                epc=tag.epc,
                alias=tag.alias,
                alias_group=tag.alias_group,
                room_number=tag.room_number,
                notes=tag.notes,
                status=tag.status,
                last_seen=last_seen_map.get(tag.epc),
            )
        )
    return response


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    payload: TagCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(_current_operator),
    _: None = Depends(csrf_protect),
):
    existing_aliases = [a for (a,) in db.query(Tag.alias).all()]
    alias = payload.alias or generate_alias(
        payload.alias_group or "male_tree", existing_aliases
    )
    if alias in existing_aliases:
        raise HTTPException(status_code=400, detail="Alias already exists")

    if db.get(Tag, payload.epc):
        raise HTTPException(status_code=400, detail="Tag already exists")

    tag = Tag(
        epc=payload.epc.strip(),
        alias=alias,
        alias_group=payload.alias_group,
        room_number=payload.room_number,
        notes=payload.notes,
        status=payload.status,
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    persist_db_to_json(db, request.app.state.known_tags_path)
    audit.log_action(db, user, "tag_create", entity_type="tag", entity_id=tag.epc, after=payload.dict())
    return TagResponse(
        epc=tag.epc,
        alias=tag.alias,
        alias_group=tag.alias_group,
        room_number=tag.room_number,
        notes=tag.notes,
        status=tag.status,
    )


@router.get("/{epc}", response_model=TagResponse)
async def get_tag(
    epc: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(_current_viewer),
):
    tag = db.get(Tag, epc)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    events_db = str(
        getattr(request.app.state, "events_db_path", None) or settings.nixstrav_events_db
    )
    last_seen_map = last_seen_for_tags(events_db, tags=[tag.epc])
    return TagResponse(
        epc=tag.epc,
        alias=tag.alias,
        alias_group=tag.alias_group,
        room_number=tag.room_number,
        notes=tag.notes,
        status=tag.status,
        last_seen=last_seen_map.get(tag.epc),
    )


@router.put("/{epc}", response_model=TagResponse)
async def update_tag(
    epc: str,
    payload: TagUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(_current_operator),
    _: None = Depends(csrf_protect),
):
    tag = db.get(Tag, epc)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    before = {
        "alias": tag.alias,
        "alias_group": tag.alias_group,
        "room_number": tag.room_number,
        "notes": tag.notes,
        "status": tag.status,
    }
    if payload.alias and payload.alias != tag.alias:
        alias_exists = (
            db.query(Tag).filter(Tag.alias == payload.alias, Tag.epc != epc).first()
        )
        if alias_exists:
            raise HTTPException(status_code=400, detail="Alias already exists")
        tag.alias = payload.alias
    if payload.alias_group is not None:
        tag.alias_group = payload.alias_group
    if payload.room_number is not None:
        tag.room_number = payload.room_number
    if payload.notes is not None:
        tag.notes = payload.notes
    if payload.status:
        tag.status = payload.status
    db.add(tag)
    db.commit()
    db.refresh(tag)
    persist_db_to_json(db, request.app.state.known_tags_path)
    audit.log_action(
        db,
        user,
        "tag_update",
        entity_type="tag",
        entity_id=tag.epc,
        before=before,
        after=payload.dict(),
    )
    return TagResponse(
        epc=tag.epc,
        alias=tag.alias,
        alias_group=tag.alias_group,
        room_number=tag.room_number,
        notes=tag.notes,
        status=tag.status,
    )


@router.delete("/{epc}")
async def delete_tag(
    epc: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(_current_operator),
    _: None = Depends(csrf_protect),
):
    tag = db.get(Tag, epc)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    before = {
        "alias": tag.alias,
        "alias_group": tag.alias_group,
        "room_number": tag.room_number,
        "notes": tag.notes,
        "status": tag.status,
    }
    tag.status = "inactive"
    db.add(tag)
    db.commit()
    persist_db_to_json(db, request.app.state.known_tags_path)
    audit.log_action(
        db,
        user,
        "tag_deactivate",
        entity_type="tag",
        entity_id=tag.epc,
        before=before,
        after={"status": "inactive"},
    )
    return {"status": "inactive"}
