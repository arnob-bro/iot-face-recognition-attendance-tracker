"""Raspberry Pi device registration and authentication routes."""

from fastapi import APIRouter, Depends

from app.api.deps import require_admin, get_current_user
from app.schemas.auth import (
    DeviceCreate,
    DeviceCreateResponse,
    DeviceLoginRequest,
    DeviceResponse,
    TokenResponse,
    UserInToken,
)
from app.services import device_service

router = APIRouter(prefix="/devices", tags=["Raspberry Pi Devices"])


@router.post("", response_model=DeviceCreateResponse, status_code=201)
async def register_device(
    data: DeviceCreate,
    _: UserInToken = Depends(require_admin),
):
    """Register a device and return its secret once."""
    return await device_service.register_device(data)


@router.get("", response_model=list[DeviceResponse])
async def list_devices(_: UserInToken = Depends(require_admin)):
    return await device_service.list_devices()


@router.put("/{device_id}/enabled", response_model=DeviceResponse)
async def set_device_enabled(
    device_id: str,
    enabled: bool,
    _: UserInToken = Depends(require_admin),
):
    return await device_service.set_device_enabled(device_id, enabled)


@router.post("/login", response_model=TokenResponse)
async def login_device(data: DeviceLoginRequest):
    return await device_service.login_device(data)


@router.get("/me", response_model=DeviceResponse)
async def get_device_me(current_user: UserInToken = Depends(get_current_user)):
    if not current_user.device_id:
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("A device token is required.")
    devices = await device_service.list_devices()
    for device in devices:
        if device.device_id == current_user.device_id:
            return device
    from app.core.exceptions import NotFoundError
    raise NotFoundError("Raspberry Pi device", current_user.device_id)
