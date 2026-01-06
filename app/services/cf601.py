from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from ..config import settings


async def _post(endpoint: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = settings.cf601d_url.rstrip("/") + endpoint
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.post(url, json=payload or {})
        resp.raise_for_status()
        return resp.json()


async def get_ports() -> Dict[str, Any]:
    return await _post("/getPorts")


async def open_device(port: str) -> Dict[str, Any]:
    return await _post("/OpenDevice", {"port": port})


async def close_device() -> Dict[str, Any]:
    return await _post("/CloseDevice")


async def get_device_params() -> Dict[str, Any]:
    return await _post("/GetDevicePara")


async def start_counting() -> Dict[str, Any]:
    return await _post("/StartCounting")


async def get_tag_info() -> Dict[str, Any]:
    return await _post("/GetTagInfo")


async def inventory_stop() -> Dict[str, Any]:
    return await _post("/InventoryStop")
