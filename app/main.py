from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .database import Base, engine, SessionLocal
from .routers import api, views
from .services.known_tags import sync_json_to_db
from .services.users import ensure_admin_exists


Base.metadata.create_all(bind=engine)

app = FastAPI(title="nixstrav-mng", version="0.1.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie=settings.security.session_cookie,
    same_site=settings.security.session_samesite,
    https_only=settings.security.session_secure,
)

# LAN-only, but keep a minimal CORS safe baseline
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

static_dir = Path(__file__).parent / "static"
templates_dir = Path(__file__).parent / "templates"

templates = Jinja2Templates(directory=str(templates_dir))
templates.env.globals["settings"] = settings

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.state.events_db_path = settings.nixstrav_events_db
app.state.known_tags_path = settings.nixstrav_known_tags_json


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    app.state.events_db_path = settings.nixstrav_events_db
    app.state.known_tags_path = settings.nixstrav_known_tags_json
    session = SessionLocal()
    try:
        sync_json_to_db(session, settings.nixstrav_known_tags_json)
        ensure_admin_exists(session)
    finally:
        session.close()


@app.middleware("http")
async def add_csrf_token(request: Request, call_next):
    # Ensure csrf token exists for templates
    if not request.session.get("csrf_token"):
        import secrets

        request.session["csrf_token"] = secrets.token_urlsafe(32)
    response = await call_next(request)
    return response


app.include_router(views.router)
app.include_router(api.api_router, prefix="/api/v1")
