from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import User, UserRole
from ..security import csrf_protect, require_role
from ..services import cf601

router = APIRouter()


async def _current_operator(request: Request, db: Session = Depends(get_db)) -> User:
    return await require_role(request, UserRole.operator, db)


class PortPayload(BaseModel):
    port: str


@router.post("/getPorts")
async def get_ports(user: User = Depends(_current_operator)):
    if settings.cf601_mode != "service":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CF601 not in service mode")
    return await cf601.get_ports()


@router.post("/OpenDevice")
async def open_device(
    payload: PortPayload,
    user: User = Depends(_current_operator),
    _: None = Depends(csrf_protect),
):
    if settings.cf601_mode != "service":
        raise HTTPException(status_code=400, detail="CF601 not in service mode")
    return await cf601.open_device(payload.port)


@router.post("/CloseDevice")
async def close_device(
    user: User = Depends(_current_operator),
    _: None = Depends(csrf_protect),
):
    if settings.cf601_mode != "service":
        raise HTTPException(status_code=400, detail="CF601 not in service mode")
    return await cf601.close_device()


@router.post("/GetDevicePara")
async def get_device_para(user: User = Depends(_current_operator)):
    if settings.cf601_mode != "service":
        raise HTTPException(status_code=400, detail="CF601 not in service mode")
    return await cf601.get_device_params()


@router.post("/StartCounting")
async def start_counting(
    user: User = Depends(_current_operator),
    _: None = Depends(csrf_protect),
):
    if settings.cf601_mode != "service":
        raise HTTPException(status_code=400, detail="CF601 not in service mode")
    return await cf601.start_counting()


@router.post("/GetTagInfo")
async def get_tag_info(user: User = Depends(_current_operator)):
    if settings.cf601_mode != "service":
        raise HTTPException(status_code=400, detail="CF601 not in service mode")
    return await cf601.get_tag_info()


@router.post("/InventoryStop")
async def inventory_stop(
    user: User = Depends(_current_operator),
    _: None = Depends(csrf_protect),
):
    if settings.cf601_mode != "service":
        raise HTTPException(status_code=400, detail="CF601 not in service mode")
    return await cf601.inventory_stop()
