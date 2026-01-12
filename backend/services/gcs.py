"""
Google Cloud Storage utilities for video upload/download.
"""
import logging
import os
import uuid
from datetime import timedelta
from typing import Optional

import subprocess

from google.cloud import storage
from google.auth import default, impersonated_credentials
from google.auth.transport import requests as google_requests
from google.oauth2.credentials import Credentials as OAuthCredentials

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
    # ADC credentials differ from gcloud credentials, so we use gcloud's token directly
    target_service_account = os.getenv(
        "GCS_SIGNING_SERVICE_ACCOUNT",
        "268399199868-compute@developer.gserviceaccount.com"
    )

    try:
        # First try with ADC credentials
        logger.info(f"Trying impersonated credentials with SA: {target_service_account}")
        impersonated = impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=target_service_account,
            target_scopes=['https://www.googleapis.com/auth/cloud-platform'],
        )
        # Test if signing works
        impersonated.sign_bytes(b"test")
        logger.info("ADC impersonation works")
        _signing_credentials = impersonated
        return _signing_credentials
    except Exception as e:
        logger.warning(f"ADC impersonation failed: {e}")

    # Fallback: Use gcloud CLI token (works when gcloud has different auth than ADC)
    try:
        logger.info("Falling back to gcloud CLI credentials")
        result = subprocess.run(
            ['gcloud', 'auth', 'print-access-token'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            access_token = result.stdout.strip()
            gcloud_creds = OAuthCredentials(token=access_token)
            impersonated = impersonated_credentials.Credentials(
                source_credentials=gcloud_creds,
                target_principal=target_service_account,
                target_scopes=['https://www.googleapis.com/auth/cloud-platform'],
            )
            # Test if signing works
            impersonated.sign_bytes(b"test")
            logger.info("gcloud CLI impersonation works")
            _signing_credentials = impersonated
            return _signing_credentials
    except Exception as e:
        logger.warning(f"gcloud CLI fallback failed: {e}")

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

    # Note: Skipping blob.exists() check because ADC may not have direct read access
    # The signed URL will fail at download time if object doesn't exist

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


def download_to_temp(object_name: str, temp_dir: Optional[str] = None) -> str:
    """
    Download a GCS object to a temporary file using a signed URL.

    Args:
        object_name: The object name in GCS (e.g., "videos/abc123.mp4")
        temp_dir: Optional temp directory to use

    Returns:
        Path to the downloaded file

    Raises:
        ValueError: If download fails
    """
    import tempfile
    import requests

    # Generate a signed download URL (works even without direct read access)
    credentials = get_signing_credentials()
    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(object_name)

    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=30),
        method="GET",
        credentials=credentials,
    )

    # Create temp file with same extension
    extension = os.path.splitext(object_name)[1] or ".mp4"
    fd, temp_path = tempfile.mkstemp(suffix=extension, dir=temp_dir)
    os.close(fd)

    logger.info(f"Downloading {object_name} via signed URL to {temp_path}")

    # Download using the signed URL with timeout and retry
    # Large videos (500MB) may take several minutes to download
    max_retries = 3
    timeout = (30, 600)  # (connect timeout, read timeout) - 10 min read for large files

    for attempt in range(max_retries):
        try:
            response = requests.get(signed_url, stream=True, timeout=timeout)
            if response.status_code != 200:
                raise ValueError(f"Failed to download {object_name}: {response.status_code} {response.reason}")

            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=65536):  # 64KB chunks for faster download
                    f.write(chunk)
            break  # Success, exit retry loop

        except requests.exceptions.Timeout as e:
            logger.warning(f"Download timeout (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise ValueError(f"Download timed out after {max_retries} attempts")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Download error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise ValueError(f"Download failed after {max_retries} attempts: {e}")

    logger.info(f"Download complete: {os.path.getsize(temp_path)} bytes")

    return temp_path
