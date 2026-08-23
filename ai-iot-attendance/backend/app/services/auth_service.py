"""
Authentication service — handles login, registration, and user lookup.

All password hashing and JWT creation is delegated to the security module.
User data (teachers/admins) is stored in the Firebase 'teachers' collection.
"""

import logging
from datetime import datetime, timezone

from app.core.firebase import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import (
    AuthenticationError,
    DuplicateError,
    NotFoundError,
)
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    TeacherCreate,
    TeacherResponse,
    UserInToken,
)

logger = logging.getLogger(__name__)

TEACHERS_COLLECTION = "teachers"


async def login(request: LoginRequest) -> TokenResponse:
    """
    Authenticate a teacher/admin and return a JWT token.

    Looks up the user by email, verifies the password hash,
    and creates a signed JWT with their role.
    """
    db = get_db()
    docs = (
        db.collection(TEACHERS_COLLECTION)
        .where("email", "==", request.email)
        .limit(1)
        .get()
    )

    if not docs:
        raise AuthenticationError("Invalid email or password.")

    doc = docs[0]
    user_data = doc.to_dict()

    if not verify_password(request.password, user_data["password_hash"]):
        raise AuthenticationError("Invalid email or password.")

    # Create JWT with user identity claims
    token = create_access_token(
        data={
            "sub": doc.id,
            "email": user_data["email"],
            "role": user_data["role"],
        }
    )

    return TokenResponse(
        access_token=token,
        role=user_data["role"],
        name=user_data["name"],
    )


async def register_teacher(data: TeacherCreate) -> TeacherResponse:
    """
    Create a new teacher or admin account.

    Checks for duplicate emails before creating.
    Passwords are hashed with bcrypt before storage.
    """
    db = get_db()

    # Check for duplicate email
    existing = (
        db.collection(TEACHERS_COLLECTION)
        .where("email", "==", data.email)
        .limit(1)
        .get()
    )
    if existing:
        raise DuplicateError("Teacher", data.email)

    now = datetime.now(timezone.utc).isoformat()
    doc_data = {
        "name": data.name,
        "email": data.email,
        "password_hash": hash_password(data.password),
        "role": data.role,
        "created_at": now,
    }

    doc_ref = db.collection(TEACHERS_COLLECTION).add(doc_data)
    teacher_id = doc_ref[1].id

    logger.info(f"Created teacher: {data.email} (role={data.role})")

    return TeacherResponse(
        teacher_id=teacher_id,
        name=data.name,
        email=data.email,
        role=data.role,
        created_at=now,
    )


async def get_current_user(user_id: str) -> TeacherResponse:
    """Get teacher profile by document ID."""
    db = get_db()
    doc = db.collection(TEACHERS_COLLECTION).document(user_id).get()

    if not doc.exists:
        raise NotFoundError("Teacher", user_id)

    data = doc.to_dict()
    return TeacherResponse(
        teacher_id=doc.id,
        name=data["name"],
        email=data["email"],
        role=data["role"],
        created_at=data.get("created_at"),
    )


async def bootstrap_admin(email: str, password: str, name: str) -> None:
    """
    Create the initial admin account if no admins exist.

    Called once during application startup. Safe to call multiple times —
    it will skip if an admin already exists.
    """
    db = get_db()
    existing = (
        db.collection(TEACHERS_COLLECTION)
        .where("role", "==", "admin")
        .limit(1)
        .get()
    )

    if existing:
        logger.info("Admin account already exists, skipping bootstrap.")
        return

    await register_teacher(
        TeacherCreate(
            name=name,
            email=email,
            password=password,
            role="admin",
        )
    )
    logger.info(f"Bootstrapped admin account: {email}")
