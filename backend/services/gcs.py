"""
Google Cloud Storage utilities for video upload/download.

Authentication strategy:
- On Cloud Run: Uses the default service account directly
- Locally: Uses gcloud CLI credentials to impersonate the github-actions service account
  (This avoids conflicts with ADC which may be configured for other tools like Claude/Vertex AI)
"""
import logging
import os
import subprocess
import uuid
from datetime import timedelta
from typing import Optional

from google.cloud import storage
from google.auth import default, impersonated_credentials
from google.oauth2.credentials import Credentials as OAuthCredentials

logger = logging.getLogger(__name__)

# Configuration
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "forging-uploads")
UPLOAD_URL_EXPIRY_MINUTES = 15
DOWNLOAD_URL_EXPIRY_MINUTES = 60

# File limits
MAX_VIDEO_SIZE_MB = 700
MAX_REPLAY_SIZE_MB = 500  # Demo files can be large (168MB+)
MAX_DURATION_SECONDS = 1800  # 30 minutes
ALLOWED_VIDEO_CONTENT_TYPES = ["video/mp4"]
ALLOWED_REPLAY_CONTENT_TYPES = ["application/octet-stream"]

# Service account for impersonation (shared with Firestore)
TARGET_SERVICE_ACCOUNT = os.getenv(
    "GCP_SERVICE_ACCOUNT",
    "github-actions@project-48dfd3a0-58cd-43e5-ae7.iam.gserviceaccount.com"
)

# Cache the client and credentials
_storage_client = None
_signing_credentials = None


def is_running_on_cloud_run() -> bool:
    """Check if we're running on Cloud Run (or other GCP compute environment)."""
    # Cloud Run sets K_SERVICE environment variable
    return os.getenv("K_SERVICE") is not None


def get_signing_credentials():
    """
    Get credentials that can sign URLs.

    Priority:
    1. GOOGLE_APPLICATION_CREDENTIALS env var (service account key file)
    2. Cloud Run default service account (with IAM signing)
    3. gcloud CLI impersonation (legacy, requires frequent re-auth)

    Requires (impersonation only): Your gcloud account must have roles/iam.serviceAccountTokenCreator
    on the target service account.
    """
    global _signing_credentials
    if _signing_credentials is not None:
        return _signing_credentials

    # Priority 1: Service account key file (recommended for local dev)
    key_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if key_file and os.path.exists(key_file):
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_file(
            key_file,
            scopes=['https://www.googleapis.com/auth/cloud-platform'],
        )
        logger.info(f"Using service account key file: {key_file}")
        _signing_credentials = credentials
        return _signing_credentials

    # Priority 2: Cloud Run - use impersonated credentials for signing
    if is_running_on_cloud_run():
        source_credentials, project = default()
        logger.info("Running on Cloud Run, using IAM signing credentials")
        # Create impersonated credentials that can sign
        # The Cloud Run SA impersonates itself to get signing capability
        impersonated = impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=TARGET_SERVICE_ACCOUNT,
            target_scopes=['https://www.googleapis.com/auth/cloud-platform'],
        )
        _signing_credentials = impersonated
        return _signing_credentials

    # Priority 3: gcloud CLI impersonation (legacy fallback)
    local_dev_account = os.getenv("GCP_LOCAL_ACCOUNT")
    if not local_dev_account:
        raise ValueError(
            "No credentials available. Set GOOGLE_APPLICATION_CREDENTIALS to a service account key file, "
            "or set GCP_LOCAL_ACCOUNT for gcloud impersonation."
        )

    logger.info(f"Local dev: Using gcloud CLI ({local_dev_account}) to impersonate {TARGET_SERVICE_ACCOUNT}")
    result = subprocess.run(
        ['gcloud', 'auth', 'print-access-token', f'--account={local_dev_account}'],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        raise ValueError(f"Failed to get gcloud access token: {result.stderr}")

    access_token = result.stdout.strip()
    gcloud_creds = OAuthCredentials(token=access_token)

    impersonated = impersonated_credentials.Credentials(
        source_credentials=gcloud_creds,
        target_principal=TARGET_SERVICE_ACCOUNT,
        target_scopes=['https://www.googleapis.com/auth/cloud-platform'],
    )
    # Verify signing works
    impersonated.sign_bytes(b"test")
    logger.info("Impersonation successful")
    _signing_credentials = impersonated
    return _signing_credentials


def get_storage_client() -> storage.Client:
    """Get GCS client with appropriate credentials."""
    global _storage_client
    if _storage_client is None:
        credentials = get_signing_credentials()
        _storage_client = storage.Client(credentials=credentials)
    return _storage_client


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
    if content_type not in ALLOWED_VIDEO_CONTENT_TYPES:
        raise ValueError(
            f"Invalid content type: {content_type}. "
            f"Allowed: {ALLOWED_VIDEO_CONTENT_TYPES}"
        )

    # Validate file size if provided
    if file_size is not None:
        max_bytes = MAX_VIDEO_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise ValueError(
                f"File too large: {file_size / 1024 / 1024:.1f}MB. "
                f"Max: {MAX_VIDEO_SIZE_MB}MB"
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


def generate_replay_upload_url(
    filename: str,
    file_size: Optional[int] = None,
) -> dict:
    """
    Generate a signed URL for uploading a replay/demo file to GCS.

    Args:
        filename: Original filename (used for extension validation)
        file_size: File size in bytes (optional, for validation)

    Returns:
        dict with signed_url, object_name, and expiry_minutes

    Raises:
        ValueError: If file extension is not allowed or file too large
    """
    # Validate file extension
    extension = os.path.splitext(filename)[1].lower()
    allowed_extensions = [".aoe2record", ".dem"]
    if extension not in allowed_extensions:
        raise ValueError(
            f"Invalid file extension: {extension}. "
            f"Allowed: {allowed_extensions}"
        )

    # Validate file size if provided
    if file_size is not None:
        max_bytes = MAX_REPLAY_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise ValueError(
                f"File too large: {file_size / 1024 / 1024:.1f}MB. "
                f"Max: {MAX_REPLAY_SIZE_MB}MB"
            )

    # Generate unique object name
    object_name = f"replays/{uuid.uuid4()}{extension}"

    # Get signing credentials
    credentials = get_signing_credentials()

    # Get bucket and blob
    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(object_name)

    # Generate signed URL for upload (PUT)
    # Use application/octet-stream for binary files
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=UPLOAD_URL_EXPIRY_MINUTES),
        method="PUT",
        content_type="application/octet-stream",
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
    Generate a public URL for downloading/playing a file from GCS.

    The bucket is configured with public read access (allUsers has objectViewer),
    so we can use direct public URLs instead of signed URLs for much faster performance.

    Args:
        object_name: The object name in GCS (e.g., "videos/abc123.mp4")

    Returns:
        dict with signed_url (actually a public URL) and expiry_minutes

    Raises:
        ValueError: If object doesn't exist
    """
    # Use public URL - bucket has allUsers objectViewer permission
    # This is much faster than generating signed URLs
    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_name}"

    return {
        "signed_url": public_url,  # Keep key name for API compatibility
        "object_name": object_name,
        "expiry_minutes": None,  # Public URLs don't expire
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


def upload_file(local_path: str, object_name: str, content_type: str = "image/jpeg") -> str:
    """
    Upload a local file to GCS.

    Args:
        local_path: Path to the local file
        object_name: The object name in GCS (e.g., "thumbnails/abc123.jpg")
        content_type: MIME type of the file

    Returns:
        The object name in GCS

    Raises:
        ValueError: If upload fails
    """
    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(object_name)

    logger.info(f"Uploading {local_path} to gs://{BUCKET_NAME}/{object_name}")
    blob.upload_from_filename(local_path, content_type=content_type)
    logger.info(f"Upload complete: {object_name}")

    return object_name


def download_to_temp(object_name: str, temp_dir: Optional[str] = None) -> str:
    """
    Download a GCS object to a temporary file using a signed URL.

    NOTE: This is a synchronous blocking function. For async contexts,
    use download_to_temp_async() instead.

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

    logger.info(f"[GAME-ANALYSIS] Downloading {object_name} via signed URL to {temp_path}")

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
            logger.warning(f"[GAME-ANALYSIS] Download timeout (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise ValueError(f"Download timed out after {max_retries} attempts")
        except requests.exceptions.RequestException as e:
            logger.warning(f"[GAME-ANALYSIS] Download error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise ValueError(f"Download failed after {max_retries} attempts: {e}")

    logger.info(f"[GAME-ANALYSIS] Download complete: {os.path.getsize(temp_path)} bytes")

    return temp_path


async def download_to_temp_async(object_name: str, temp_dir: Optional[str] = None) -> str:
    """
    Async version of download_to_temp that doesn't block the event loop.

    Runs the synchronous download in a thread pool.

    Args:
        object_name: The object name in GCS (e.g., "videos/abc123.mp4")
        temp_dir: Optional temp directory to use

    Returns:
        Path to the downloaded file

    Raises:
        ValueError: If download fails
    """
    import asyncio
    return await asyncio.to_thread(download_to_temp, object_name, temp_dir)
