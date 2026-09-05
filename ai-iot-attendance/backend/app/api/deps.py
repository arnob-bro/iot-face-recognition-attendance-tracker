"""
Dependency injection — shared dependencies for API routes.

Provides the `get_current_user` dependency that extracts and validates
the JWT token from the Authorization header, and role-checking dependencies.
"""

from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_access_token
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.schemas.auth import UserInToken

# FastAPI security scheme — extracts Bearer token from header.
# auto_error=False allows us to distinguish between a missing token
# (authorization failure -> 403) and a malformed/expired token (401).
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> UserInToken:
    """
    Validate the JWT token and return the current user identity.

    This is the primary authentication dependency — inject it into
    any route that requires a logged-in user.
    """
    if credentials is None:
        raise AuthorizationError("Authentication required.")

    payload = decode_access_token(credentials.credentials)

    if payload is None:
        raise AuthenticationError("Invalid or expired token.")

    return UserInToken(
        user_id=payload.get("sub", ""),
        email=payload.get("email", ""),
        role=payload.get("role", ""),
    )


async def require_admin(
    current_user: UserInToken = Depends(get_current_user),
) -> UserInToken:
    """
    Dependency that requires the current user to be an admin.

    Use this for routes that should only be accessible to administrators.
    """
    if current_user.role != "admin":
        raise AuthorizationError(
            "This action requires admin privileges."
        )
    return current_user


async def require_teacher_or_admin(
    current_user: UserInToken = Depends(get_current_user),
) -> UserInToken:
    """
    Dependency that requires the current user to be a teacher or admin.
    """
    if current_user.role not in ("admin", "teacher"):
        raise AuthorizationError(
            "This action requires teacher or admin privileges."
        )
    return current_user
