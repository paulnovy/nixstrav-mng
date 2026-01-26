from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Tag, User, UserRole
from ..security import (
    csrf_protect,
    get_or_create_csrf,
    login_limiter,
    require_role,
    require_user,
)
from ..services import audit
from ..services.alias_generator import generate_alias
from ..services.epc import normalize_epc
from ..services.events import (
    EventFilters,
    events_for_reader,
    events_for_tag,
    latest_events,
    list_events,
    unknown_tags,
)
from ..services.known_tags import persist_db_to_json
from ..services.system_status import check_service_status, reader_status_heuristic
from ..services.users import authenticate_user, create_user, get_user_by_username

router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
templates.env.globals["settings"] = settings


async def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    return await require_user(request, db)


async def current_operator(request: Request, db: Session = Depends(get_db)) -> User:
    return await require_role(request, UserRole.operator, db)


async def current_admin(request: Request, db: Session = Depends(get_db)) -> User:
    return await require_role(request, UserRole.admin, db)


def _redirect(path: str) -> RedirectResponse:
    return RedirectResponse(url=path, status_code=status.HTTP_302_FOUND)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    if request.session.get("user_id"):
        return _redirect("/")
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "csrf_token": get_or_create_csrf(request), "error": None},
    )


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    _: None = Depends(csrf_protect),
):
    ip = request.client.host if request.client else "unknown"
    username_clean = username.strip()
    if login_limiter.is_locked(username_clean, ip):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Konto zablokowane – spróbuj za chwilę.",
                "csrf_token": get_or_create_csrf(request),
            },
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    user = authenticate_user(db, username_clean, password)
    if not user:
        login_limiter.register_failure(username_clean, ip)
        audit.log_action(db, None, "login_failed", entity_id=username_clean, ip=ip)
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Błędny login lub hasło",
                "csrf_token": get_or_create_csrf(request),
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    login_limiter.register_success(username_clean, ip)
    request.session.clear()
    request.session["user_id"] = user.id
    request.session["role"] = user.role
    request.session["csrf_token"] = get_or_create_csrf(request)
    audit.log_action(db, user, "login", entity_id=user.username, ip=ip)
    return _redirect("/")


@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(csrf_protect),
):
    user = None
    if request.session.get("user_id"):
        user = db.get(User, int(request.session["user_id"]))
    request.session.clear()
    audit.log_action(db, user, "logout", entity_id=user.username if user else None)
    return _redirect("/login")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user: User = Depends(current_user)):
    events_db = str(request.app.state.events_db_path)
    overview_events = latest_events(events_db, limit=20)
    unknown = unknown_tags(events_db, limit=10)
    reader_state = reader_status_heuristic(events_db)
    problems = [e for e in overview_events if e.get("reason") in ("relay_error", "unknown_tag")]
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "events": overview_events,
            "unknown": unknown,
            "readers": reader_state,
            "problems": problems,
            "csrf_token": get_or_create_csrf(request),
        },
    )


@router.get("/tags", response_class=HTMLResponse)
async def tags_list(
    request: Request,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    stmt = select(Tag)
    if status_filter:
        stmt = stmt.where(Tag.status == status_filter)
    tags = db.scalars(stmt).all()
    return templates.TemplateResponse(
        "tags.html",
        {
            "request": request,
            "tags": tags,
            "user": user,
            "status_filter": status_filter or "",
            "csrf_token": get_or_create_csrf(request),
        },
    )


@router.get("/tags/new", response_class=HTMLResponse)
async def tags_new_form(
    request: Request,
    user: User = Depends(current_operator),
):
    return templates.TemplateResponse(
        "tag_form.html",
        {
            "request": request,
            "tag": None,
            "mode": "create",
            "user": user,
            "csrf_token": get_or_create_csrf(request),
        },
    )


@router.post("/tags/new")
async def tags_create(
    request: Request,
    epc: str = Form(...),
    alias: Optional[str] = Form(None),
    alias_group: Optional[str] = Form(None),
    room_number: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    status_value: str = Form("active"),
    db: Session = Depends(get_db),
    user: User = Depends(current_operator),
    _: None = Depends(csrf_protect),
):
    canonical_epc = normalize_epc(epc)
    if not canonical_epc:
        return templates.TemplateResponse(
            "tag_form.html",
            {
                "request": request,
                "tag": None,
                "mode": "create",
                "user": user,
                "error": "Nieprawidłowy EPC",
                "csrf_token": get_or_create_csrf(request),
            },
            status_code=400,
        )
    existing_aliases = [a for (a,) in db.query(Tag.alias).all()]
    alias_group_value = alias_group or "male_tree"
    use_alias = alias or generate_alias(alias_group_value, existing_aliases)
    if use_alias in existing_aliases:
        error = "Alias już istnieje"
        return templates.TemplateResponse(
            "tag_form.html",
            {
                "request": request,
                "tag": None,
                "mode": "create",
                "user": user,
                "error": error,
                "csrf_token": get_or_create_csrf(request),
            },
            status_code=400,
        )
    if db.get(Tag, canonical_epc):
        error = "Tag już istnieje"
        return templates.TemplateResponse(
            "tag_form.html",
            {
                "request": request,
                "tag": None,
                "mode": "create",
                "user": user,
                "error": error,
                "csrf_token": get_or_create_csrf(request),
            },
            status_code=400,
        )
    tag = Tag(
        epc=canonical_epc,
        alias=use_alias,
        alias_group=alias_group or None,
        room_number=room_number,
        notes=notes,
        status=status_value,
    )
    db.add(tag)
    db.commit()
    persist_db_to_json(db, request.app.state.known_tags_path)
    audit.log_action(
        db,
        user,
        "tag_create",
        entity_type="tag",
        entity_id=tag.epc,
        after={
            "alias": tag.alias,
            "alias_group": tag.alias_group,
            "room_number": tag.room_number,
            "notes": tag.notes,
            "status": tag.status,
        },
    )
    return _redirect("/tags")


@router.get("/tags/{epc}", response_class=HTMLResponse)
async def tag_detail(
    epc: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    tag = db.get(Tag, epc)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    events_db = str(request.app.state.events_db_path)
    tag_events = events_for_tag(events_db, tag.epc, limit=20)
    reader_events = []
    if tag_events:
        reader_events = events_for_reader(events_db, tag_events[0]["reader_id"], limit=20)
    return templates.TemplateResponse(
        "tag_detail.html",
        {
            "request": request,
            "tag": tag,
            "tag_events": tag_events,
            "reader_events": reader_events,
            "user": user,
            "csrf_token": get_or_create_csrf(request),
        },
    )


@router.post("/tags/{epc}")
async def tag_update(
    epc: str,
    request: Request,
    alias: Optional[str] = Form(None),
    alias_group: Optional[str] = Form(None),
    room_number: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    status_value: str = Form("active"),
    db: Session = Depends(get_db),
    user: User = Depends(current_operator),
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
    if alias and alias != tag.alias:
        existing = (
            db.query(Tag).filter(Tag.alias == alias, Tag.epc != epc).first()
        )
        if existing:
            error = "Alias już istnieje"
            return templates.TemplateResponse(
                "tag_detail.html",
                {
                    "request": request,
                    "tag": tag,
                    "tag_events": [],
                    "reader_events": [],
                    "user": user,
                    "error": error,
                    "csrf_token": get_or_create_csrf(request),
                },
                status_code=400,
            )
        tag.alias = alias
    tag.alias_group = alias_group or None
    tag.room_number = room_number
    tag.notes = notes
    tag.status = status_value
    db.add(tag)
    db.commit()
    persist_db_to_json(db, request.app.state.known_tags_path)
    audit.log_action(
        db,
        user,
        "tag_update",
        entity_type="tag",
        entity_id=tag.epc,
        before=before,
        after={
            "alias": tag.alias,
            "alias_group": tag.alias_group,
            "room_number": tag.room_number,
            "notes": tag.notes,
            "status": tag.status,
        },
    )
    return _redirect(f"/tags/{epc}")


@router.post("/tags/{epc}/deactivate")
async def tag_deactivate(
    epc: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_operator),
    _: None = Depends(csrf_protect),
):
    tag = db.get(Tag, epc)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    before = {"status": tag.status}
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
        after={"status": tag.status},
    )
    return _redirect(f"/tags/{epc}")


@router.get("/enroll", response_class=HTMLResponse)
async def enroll_view(
    request: Request,
    user: User = Depends(current_operator),
):
    return templates.TemplateResponse(
        "enroll.html",
        {
            "request": request,
            "user": user,
            "cf601_mode": settings.cf601_mode,
            "csrf_token": get_or_create_csrf(request),
        },
    )


@router.post("/enroll")
async def enroll_submit(
    request: Request,
    epc: str = Form(...),
    alias: Optional[str] = Form(None),
    alias_group: Optional[str] = Form("male_tree"),
    room_number: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(current_operator),
    _: None = Depends(csrf_protect),
):
    canonical_epc = normalize_epc(epc)
    if not canonical_epc:
        return templates.TemplateResponse(
            "enroll.html",
            {
                "request": request,
                "user": user,
                "cf601_mode": settings.cf601_mode,
                "error": "Nieprawidłowy EPC",
                "csrf_token": get_or_create_csrf(request),
            },
            status_code=400,
        )
    existing_aliases = [a for (a,) in db.query(Tag.alias).all()]
    alias_group_value = alias_group or "male_tree"
    use_alias = alias or generate_alias(alias_group_value, existing_aliases)
    if use_alias in existing_aliases:
        return templates.TemplateResponse(
            "enroll.html",
            {
                "request": request,
                "user": user,
                "cf601_mode": settings.cf601_mode,
                "error": "Alias już istnieje",
                "csrf_token": get_or_create_csrf(request),
            },
            status_code=400,
        )
    if db.get(Tag, canonical_epc):
        error = "Tag już istnieje"
        return templates.TemplateResponse(
            "enroll.html",
            {
                "request": request,
                "user": user,
                "cf601_mode": settings.cf601_mode,
                "error": error,
                "csrf_token": get_or_create_csrf(request),
            },
            status_code=400,
        )
    tag = Tag(
        epc=canonical_epc,
        alias=use_alias,
        alias_group=alias_group_value,
        room_number=room_number,
        notes=notes,
        status="active",
    )
    db.add(tag)
    db.commit()
    persist_db_to_json(db, request.app.state.known_tags_path)
    audit.log_action(
        db,
        user,
        "tag_enroll",
        entity_type="tag",
        entity_id=tag.epc,
        after={
            "alias": tag.alias,
            "alias_group": tag.alias_group,
            "room_number": tag.room_number,
            "notes": tag.notes,
        },
    )
    return _redirect(f"/tags/{epc}")


@router.get("/events", response_class=HTMLResponse)
async def events_view(
    request: Request,
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None,
    reader_id: Optional[str] = None,
    reason: Optional[str] = None,
    tag: Optional[str] = None,
    page: int = 1,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    filters = EventFilters(
        from_ts=from_ts,
        to_ts=to_ts,
        reader_id=reader_id,
        reason=reason,
        tag=tag,
        page=page,
        page_size=50,
    )
    events_db = str(request.app.state.events_db_path)
    events, total = list_events(events_db, filters)
    return templates.TemplateResponse(
        "events.html",
        {
            "request": request,
            "events": events,
            "total": total,
            "page": page,
            "filters": filters,
            "user": user,
            "csrf_token": get_or_create_csrf(request),
        },
    )


@router.get("/system", response_class=HTMLResponse)
async def system_view(
    request: Request,
    user: User = Depends(current_user),
):
    events_db = str(request.app.state.events_db_path)
    readers = reader_status_heuristic(events_db)
    services = [
        check_service_status("rfid-server.service"),
        check_service_status("nixstrav-mng.service"),
    ]
    return templates.TemplateResponse(
        "system.html",
        {
            "request": request,
            "user": user,
            "readers": readers,
            "services": services,
            "csrf_token": get_or_create_csrf(request),
        },
    )


@router.get("/settings/users", response_class=HTMLResponse)
async def users_view(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_admin),
):
    users = db.scalars(select(User)).all()
    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "user": user,
            "users": users,
            "csrf_token": get_or_create_csrf(request),
        },
    )


@router.post("/settings/users/new")
async def users_new(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("viewer"),
    db: Session = Depends(get_db),
    user: User = Depends(current_admin),
    _: None = Depends(csrf_protect),
):
    existing = get_user_by_username(db, username)
    if existing:
        users = db.scalars(select(User)).all()
        return templates.TemplateResponse(
            "users.html",
            {
                "request": request,
                "user": user,
                "users": users,
                "error": "Użytkownik już istnieje",
                "csrf_token": get_or_create_csrf(request),
            },
            status_code=400,
        )
    create_user(db, username=username, password=password, role=UserRole(role))
    audit.log_action(
        db,
        user,
        "user_create",
        entity_type="user",
        entity_id=username,
        after={"role": role},
    )
    return _redirect("/settings/users")
