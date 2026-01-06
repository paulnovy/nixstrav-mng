from fastapi import APIRouter

from . import api_auth, api_tags, api_events, api_system, api_cf601

api_router = APIRouter()
api_router.include_router(api_auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(api_tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(api_events.router, prefix="/events", tags=["events"])
api_router.include_router(api_system.router, prefix="/system", tags=["system"])
api_router.include_router(api_cf601.router, prefix="/cf601", tags=["cf601"])
