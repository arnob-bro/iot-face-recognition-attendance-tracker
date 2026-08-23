"""
Firebase Firestore client initialization.

Provides a singleton Firestore client that is initialized once
using the service account credentials from the environment.
"""

import firebase_admin
from firebase_admin import credentials, firestore
from app.core.config import settings
import os
import logging

logger = logging.getLogger(__name__)

# Firebase app singleton — initialized once
_firebase_app = None
_firestore_client = None


def init_firebase() -> None:
    """
    Initialize the Firebase Admin SDK.

    Must be called once at application startup (in the FastAPI lifespan).
    Uses the service account credentials file specified in the config.
    """
    global _firebase_app, _firestore_client

    if _firebase_app is not None:
        logger.info("Firebase already initialized, skipping.")
        return

    cred_path = settings.firebase_credentials_path

    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        _firebase_app = firebase_admin.initialize_app(cred, {
            "projectId": settings.firebase_project_id,
        })
        logger.info(
            f"Firebase initialized with credentials from {cred_path}"
        )
    else:
        # For development/testing without a real credentials file,
        # attempt to use Application Default Credentials or emulator.
        logger.warning(
            f"Firebase credentials file not found at '{cred_path}'. "
            "Attempting to initialize with Application Default Credentials. "
            "Set FIRESTORE_EMULATOR_HOST for local emulator usage."
        )
        try:
            _firebase_app = firebase_admin.initialize_app(options={
                "projectId": settings.firebase_project_id,
            })
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise

    _firestore_client = firestore.client()
    logger.info("Firestore client ready.")


def get_db() -> firestore.firestore.Client:
    """
    Get the Firestore client instance.

    Returns:
        The initialized Firestore client.

    Raises:
        RuntimeError: If Firebase has not been initialized.
    """
    if _firestore_client is None:
        raise RuntimeError(
            "Firebase has not been initialized. "
            "Call init_firebase() during application startup."
        )
    return _firestore_client


def close_firebase() -> None:
    """Clean up Firebase resources on shutdown."""
    global _firebase_app, _firestore_client
    if _firebase_app is not None:
        firebase_admin.delete_app(_firebase_app)
        _firebase_app = None
        _firestore_client = None
        logger.info("Firebase app closed.")
