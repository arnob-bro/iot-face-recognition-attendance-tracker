"""Raspberry Pi device registration and authentication."""

import logging
import secrets
from datetime import datetime, timezone

from app.core.exceptions import AuthenticationError, DuplicateError, NotFoundError, ValidationError
from app.core.firebase import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.auth import (
    DeviceCreate,
    DeviceCreateResponse,
    DeviceLoginRequest,
    DeviceResponse,
    TokenResponse,
)

logger = logging.getLogger(__name__)

DEVICES_COLLECTION = "rpi_devices"


def _response(device_id: str, data: dict) -> DeviceResponse:
    return DeviceResponse(device_id=device_id, **data)


async def register_device(data: DeviceCreate) -> DeviceCreateResponse:
    db = get_db()
    ref = db.collection(DEVICES_COLLECTION).document(data.device_id)
    if ref.get().exists:
        raise DuplicateError("Raspberry Pi device", data.device_id)

    device_secret = secrets.token_urlsafe(32)
    device_data = {
        "name": data.name,
        "location": data.location,
        "secret_hash": hash_password(device_secret),
        "enabled": True,
        "last_seen_at": None,
    }
    ref.set(device_data)
    return DeviceCreateResponse(
        device_id=data.device_id,
        name=data.name,
        location=data.location,
        enabled=True,
        last_seen_at=None,
        device_secret=device_secret,
    )


async def list_devices() -> list[DeviceResponse]:
    db = get_db()
    return [_response(doc.id, doc.to_dict()) for doc in db.collection(DEVICES_COLLECTION).get()]


async def set_device_enabled(device_id: str, enabled: bool) -> DeviceResponse:
    db = get_db()
    ref = db.collection(DEVICES_COLLECTION).document(device_id)
    doc = ref.get()
    if not doc.exists:
        raise NotFoundError("Raspberry Pi device", device_id)
    ref.update({"enabled": enabled})
    data = doc.to_dict()
    data["enabled"] = enabled
    return _response(device_id, data)


async def login_device(data: DeviceLoginRequest) -> TokenResponse:
    db = get_db()
    ref = db.collection(DEVICES_COLLECTION).document(data.device_id)
    doc = ref.get()
    if not doc.exists:
        raise AuthenticationError("Invalid device credentials.")

    device_data = doc.to_dict()
    if not device_data.get("enabled", True):
        raise AuthenticationError("This device is disabled.")
    if not verify_password(data.device_secret, device_data["secret_hash"]):
        raise AuthenticationError("Invalid device credentials.")

    return TokenResponse(
        access_token=create_access_token({
            "sub": data.device_id,
            "email": "",
            "role": "device",
            "device_id": data.device_id,
        }),
        role="device",
        name=device_data.get("name", data.device_id),
    )


async def touch_device(device_id: str) -> None:
    db = get_db()
    ref = db.collection(DEVICES_COLLECTION).document(device_id)
    if ref.get().exists:
        ref.update({"last_seen_at": datetime.now(timezone.utc).isoformat()})


def require_device_session_access(session_data: dict, device_id: str | None) -> None:
    assigned_device_id = session_data.get("device_id")
    if device_id is None:
        return
    device_doc = get_db().collection(DEVICES_COLLECTION).document(device_id).get()
    if not device_doc.exists or not device_doc.to_dict().get("enabled", True):
        raise ValidationError("This Raspberry Pi device is disabled or unavailable.")
    if assigned_device_id != device_id:
        raise ValidationError("This device is not assigned to the session.")
    if not assigned_device_id:
        raise ValidationError("This session is not assigned to a device.")
