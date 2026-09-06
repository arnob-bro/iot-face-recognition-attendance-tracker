"""Shared schema normalization helpers."""


def normalize_timestamp(value):
    """Convert Firestore datetime-like values to API-safe ISO strings."""
    if value is None or isinstance(value, str):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
