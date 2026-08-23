"""
Custom exception classes for consistent API error responses.

These exceptions are caught by FastAPI's exception handlers and
returned as structured JSON error responses.
"""

from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    """Resource not found (404)."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} '{identifier}' not found.",
        )


class DuplicateError(HTTPException):
    """Resource already exists (409)."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource} '{identifier}' already exists.",
        )


class AuthenticationError(HTTPException):
    """Invalid credentials (401)."""

    def __init__(self, detail: str = "Invalid credentials."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Insufficient permissions (403)."""

    def __init__(self, detail: str = "Insufficient permissions."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class ValidationError(HTTPException):
    """Business logic validation failure (422)."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class ServiceUnavailableError(HTTPException):
    """External service unavailable (503)."""

    def __init__(self, service: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service} is currently unavailable. Please try again later.",
        )
