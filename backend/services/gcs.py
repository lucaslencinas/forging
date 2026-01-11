"""
Google Cloud Storage utilities for video upload/download.
"""
import logging
import os
import uuid
from datetime import timedelta
from typing import Optional

from google.cloud import storage
from google.auth import default, impersonated_credentials
from google.auth.transport import requests as google_requests

logger = logging.getLogger(__name__)

# Configuration
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "forging-uploads")
UPLOAD_URL_EXPIRY_MINUTES = 15
DOWNLOAD_URL_EXPIRY_MINUTES = 60

# File limits
MAX_FILE_SIZE_MB = 500
MAX_DURATION_SECONDS = 900  # 15 minutes
ALLOWED_CONTENT_TYPES = ["video/mp4"]

# Cache the client
_storage_client = None
_signing_credentials = None


def get_storage_client() -> storage.Client:
    """Get GCS client. Uses default credentials (ADC)."""
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client()
    return _storage_client


def get_signing_credentials():
    """
    Get credentials that can sign URLs.
    On Cloud Run, this uses the default service account.
    Locally, uses impersonation to the compute service account.
    """
    global _signing_credentials
    if _signing_credentials is not None:
        return _signing_credentials

    # Try to get default credentials
    source_credentials, project = default()

    # Check if credentials can sign directly (service account key or metadata server)
    if hasattr(source_credentials, 'sign_bytes') and hasattr(source_credentials, 'service_account_email'):
        logger.info("Using direct signing credentials")
        _signing_credentials = source_credentials
        return _signing_credentials

    # For user credentials (local dev), use impersonation
    # This requires the user to have roles/iam.serviceAccountTokenCreator on the target SA
    target_service_account = os.getenv(
        "GCS_SIGNING_SERVICE_ACCOUNT",
        "268399199868-compute@developer.gserviceaccount.com"
    )

    try:
        logger.info(f"Using impersonated credentials with SA: {target_service_account}")
        _signing_credentials = impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=target_service_account,
            target_scopes=['https://www.googleapis.com/auth/cloud-platform'],
        )
        return _signing_credentials
    except Exception as e:
        logger.warning(f"Could not create impersonated credentials: {e}")
        raise ValueError(
            "Cannot sign URLs. Ensure you have roles/iam.serviceAccountTokenCreator "
            f"on {target_service_account}"
        )


def generate_upload_url(
    filename: str,
    content_type: str,
    file_size: Optional[int] = None,
) -> dict:
    """
    Generate a signed URL for uploading a video to GCS.

    Args:
        filename: Original filename (used for extension, not stored as-is)
        content_type: MIME type (must be video/mp4)
        file_size: File size in bytes (optional, for validation)

    Returns:
        dict with signed_url, object_name, and expiry_minutes

    Raises:
        ValueError: If content_type is not allowed or file too large
    """
    # Validate content type
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(
            f"Invalid content type: {content_type}. "
            f"Allowed: {ALLOWED_CONTENT_TYPES}"
        )

    # Validate file size if provided
    if file_size is not None:
        max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise ValueError(
                f"File too large: {file_size / 1024 / 1024:.1f}MB. "
                f"Max: {MAX_FILE_SIZE_MB}MB"
            )

    # Generate unique object name
    extension = os.path.splitext(filename)[1] or ".mp4"
    object_name = f"videos/{uuid.uuid4()}{extension}"

    # Get signing credentials
    credentials = get_signing_credentials()

    # Get bucket and blob
    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(object_name)

    # Generate signed URL for upload (PUT)
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=UPLOAD_URL_EXPIRY_MINUTES),
        method="PUT",
        content_type=content_type,
        credentials=credentials,
    )

    return {
        "signed_url": signed_url,
        "object_name": object_name,
        "expiry_minutes": UPLOAD_URL_EXPIRY_MINUTES,
        "bucket": BUCKET_NAME,
    }


def generate_download_url(object_name: str) -> dict:
    """
    Generate a signed URL for downloading/playing a video from GCS.

    Args:
        object_name: The object name in GCS (e.g., "videos/abc123.mp4")

    Returns:
        dict with signed_url and expiry_minutes

    Raises:
        ValueError: If object doesn't exist
    """
    # Get signing credentials
    credentials = get_signing_credentials()

    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(object_name)

    # Check if blob exists
    if not blob.exists():
        raise ValueError(f"Object not found: {object_name}")

    # Generate signed URL for download (GET)
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=DOWNLOAD_URL_EXPIRY_MINUTES),
        method="GET",
        credentials=credentials,
    )

    return {
        "signed_url": signed_url,
        "object_name": object_name,
        "expiry_minutes": DOWNLOAD_URL_EXPIRY_MINUTES,
    }


def delete_object(object_name: str) -> bool:
    """
    Delete an object from GCS.

    Args:
        object_name: The object name in GCS

    Returns:
        True if deleted, False if not found
    """
    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(object_name)

    if blob.exists():
        blob.delete()
        return True
    return False
