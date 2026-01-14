"""
Firestore service for storing and retrieving analysis records.

Authentication strategy:
- On Cloud Run: Uses the default service account directly
- Locally: Uses gcloud CLI credentials to impersonate the github-actions service account
  (This avoids conflicts with ADC which may be configured for other tools like Claude/Vertex AI)
"""
import logging
import os
import subprocess
from datetime import datetime
from typing import Optional

from google.cloud import firestore
from google.auth import default, impersonated_credentials
from google.oauth2.credentials import Credentials as OAuthCredentials

logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-48dfd3a0-58cd-43e5-ae7")
ANALYSES_COLLECTION = "analyses"
TARGET_SERVICE_ACCOUNT = os.getenv(
    "GCP_SERVICE_ACCOUNT",
    "github-actions@project-48dfd3a0-58cd-43e5-ae7.iam.gserviceaccount.com"
)

# Cache the client
_firestore_client: Optional[firestore.Client] = None


def is_running_on_cloud_run() -> bool:
    """Check if we're running on Cloud Run."""
    # Cloud Run sets K_SERVICE environment variable
    return os.getenv("K_SERVICE") is not None


def get_credentials():
    """
    Get credentials for Firestore access.

    On Cloud Run: Uses the default service account directly (no impersonation needed).
    Locally: Uses gcloud CLI token to impersonate the service account.

    Requires (local only): Your gcloud account must have roles/iam.serviceAccountTokenCreator
    on the target service account.
    """
    # On Cloud Run, use default credentials directly
    if is_running_on_cloud_run():
        source_credentials, project = default()
        logger.info("Running on Cloud Run, using default credentials")
        return source_credentials

    # Local development: Use gcloud CLI token to impersonate the service account
    logger.info(f"Local dev: Using gcloud CLI to impersonate {TARGET_SERVICE_ACCOUNT}")
    result = subprocess.run(
        ['gcloud', 'auth', 'print-access-token'],
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
    logger.info("Impersonation successful")
    return impersonated


def get_firestore_client() -> firestore.Client:
    """Get Firestore client with appropriate credentials."""
    global _firestore_client
    if _firestore_client is None:
        credentials = get_credentials()
        _firestore_client = firestore.Client(project=PROJECT_ID, credentials=credentials)
        logger.info(f"Firestore client initialized for project: {PROJECT_ID}")
    return _firestore_client


async def save_analysis(analysis_data: dict) -> str:
    """
    Save an analysis record to Firestore.

    Args:
        analysis_data: Dictionary containing analysis record fields.
            Must include 'id' field.

    Returns:
        The analysis ID.
    """
    client = get_firestore_client()
    analysis_id = analysis_data["id"]

    # Add timestamps
    analysis_data["created_at"] = datetime.utcnow()
    analysis_data["updated_at"] = datetime.utcnow()

    # Save to Firestore
    doc_ref = client.collection(ANALYSES_COLLECTION).document(analysis_id)
    doc_ref.set(analysis_data)

    logger.info(f"Saved analysis {analysis_id} to Firestore")
    return analysis_id


async def get_analysis(analysis_id: str) -> Optional[dict]:
    """
    Retrieve an analysis record from Firestore.

    Args:
        analysis_id: The analysis ID.

    Returns:
        The analysis record as a dictionary, or None if not found.
    """
    client = get_firestore_client()
    doc_ref = client.collection(ANALYSES_COLLECTION).document(analysis_id)
    doc = doc_ref.get()

    if not doc.exists:
        logger.warning(f"Analysis {analysis_id} not found")
        return None

    data = doc.to_dict()
    # Convert Firestore timestamps to ISO strings for JSON serialization
    if "created_at" in data and hasattr(data["created_at"], "isoformat"):
        data["created_at"] = data["created_at"].isoformat()
    if "updated_at" in data and hasattr(data["updated_at"], "isoformat"):
        data["updated_at"] = data["updated_at"].isoformat()

    return data


async def list_analyses(
    limit: int = 12,
    game_type: Optional[str] = None,
    public_only: bool = True,
) -> list[dict]:
    """
    List recent analyses for the community carousel.

    Args:
        limit: Maximum number of analyses to return.
        game_type: Filter by game type (aoe2, cs2). None for all.
        public_only: Only return public analyses.

    Returns:
        List of analysis records (lightweight, for carousel display).
    """
    client = get_firestore_client()
    query = client.collection(ANALYSES_COLLECTION)

    if public_only:
        query = query.where("is_public", "==", True)

    if game_type:
        query = query.where("game_type", "==", game_type)

    query = query.order_by("created_at", direction=firestore.Query.DESCENDING)
    query = query.limit(limit)

    docs = query.stream()

    analyses = []
    for doc in docs:
        data = doc.to_dict()
        # Return lightweight data for carousel
        analyses.append({
            "id": data.get("id"),
            "game_type": data.get("game_type"),
            "title": data.get("title"),
            "creator_name": data.get("creator_name"),
            "thumbnail_url": data.get("thumbnail_url"),
            "tips_count": data.get("tips_count", 0),
            "created_at": data.get("created_at").isoformat() if hasattr(data.get("created_at"), "isoformat") else data.get("created_at"),
        })

    logger.info(f"Listed {len(analyses)} analyses")
    return analyses


async def delete_analysis(analysis_id: str) -> bool:
    """
    Delete an analysis record from Firestore.

    Args:
        analysis_id: The analysis ID.

    Returns:
        True if deleted, False if not found.
    """
    client = get_firestore_client()
    doc_ref = client.collection(ANALYSES_COLLECTION).document(analysis_id)
    doc = doc_ref.get()

    if not doc.exists:
        return False

    doc_ref.delete()
    logger.info(f"Deleted analysis {analysis_id}")
    return True


async def update_analysis(analysis_id: str, updates: dict) -> bool:
    """
    Update an analysis record in Firestore.

    Args:
        analysis_id: The analysis ID.
        updates: Dictionary of fields to update.

    Returns:
        True if updated, False if not found.
    """
    client = get_firestore_client()
    doc_ref = client.collection(ANALYSES_COLLECTION).document(analysis_id)
    doc = doc_ref.get()

    if not doc.exists:
        return False

    updates["updated_at"] = datetime.utcnow()
    doc_ref.update(updates)
    logger.info(f"Updated analysis {analysis_id}")
    return True
