#!/usr/bin/env python3
"""
Cleanup script to delete all analyses from Firestore and GCS.

Usage:
    python cleanup_analyses.py              # Dry run (show what would be deleted)
    python cleanup_analyses.py --execute    # Actually delete everything
"""
import argparse
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from google.cloud import firestore as firestore_lib
from services.firestore import get_firestore_client, ANALYSES_COLLECTION
from services.gcs import get_storage_client, BUCKET_NAME


def list_all_analyses() -> list[dict]:
    """List all analyses from Firestore (not just public ones)."""
    client = get_firestore_client()
    docs = client.collection(ANALYSES_COLLECTION).stream()

    analyses = []
    for doc in docs:
        data = doc.to_dict()
        analyses.append({
            "id": data.get("id"),
            "title": data.get("title"),
            "game_type": data.get("game_type"),
            "video_object_name": data.get("video_object_name"),
            "replay_object_name": data.get("replay_object_name"),
            "thumbnail_url": data.get("thumbnail_url"),
            "audio_object_names": data.get("audio_object_names", []),
        })

    return analyses


def delete_gcs_object(object_name: str, dry_run: bool) -> bool:
    """Delete a single object from GCS."""
    if not object_name:
        return False

    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(object_name)

    if not blob.exists():
        logger.info(f"  [SKIP] GCS object not found: {object_name}")
        return False

    if dry_run:
        logger.info(f"  [DRY RUN] Would delete GCS: {object_name}")
    else:
        blob.delete()
        logger.info(f"  [DELETED] GCS: {object_name}")

    return True


def delete_firestore_doc(analysis_id: str, dry_run: bool) -> bool:
    """Delete a Firestore document."""
    client = get_firestore_client()
    doc_ref = client.collection(ANALYSES_COLLECTION).document(analysis_id)

    if dry_run:
        logger.info(f"  [DRY RUN] Would delete Firestore doc: {analysis_id}")
    else:
        doc_ref.delete()
        logger.info(f"  [DELETED] Firestore doc: {analysis_id}")

    return True


def cleanup_all(dry_run: bool = True):
    """Delete all analyses from Firestore and their associated GCS objects."""
    logger.info(f"{'DRY RUN - ' if dry_run else ''}Starting cleanup...")

    analyses = list_all_analyses()

    if not analyses:
        logger.info("No analyses found. Nothing to clean up.")
        return

    logger.info(f"Found {len(analyses)} analyses to delete")

    stats = {
        "analyses": 0,
        "videos": 0,
        "replays": 0,
        "thumbnails": 0,
        "audio_files": 0,
    }

    for analysis in analyses:
        analysis_id = analysis["id"]
        logger.info(f"\nProcessing: {analysis_id} - {analysis.get('title', 'Untitled')}")

        # Delete video from GCS
        if analysis.get("video_object_name"):
            if delete_gcs_object(analysis["video_object_name"], dry_run):
                stats["videos"] += 1

        # Delete replay from GCS
        if analysis.get("replay_object_name"):
            if delete_gcs_object(analysis["replay_object_name"], dry_run):
                stats["replays"] += 1

        # Delete thumbnail from GCS
        thumbnail_url = analysis.get("thumbnail_url")
        if thumbnail_url and thumbnail_url.startswith("thumbnails/"):
            if delete_gcs_object(thumbnail_url, dry_run):
                stats["thumbnails"] += 1

        # Delete audio files from GCS
        for audio_object in analysis.get("audio_object_names", []):
            if delete_gcs_object(audio_object, dry_run):
                stats["audio_files"] += 1

        # Delete Firestore document
        if delete_firestore_doc(analysis_id, dry_run):
            stats["analyses"] += 1

    logger.info("\n" + "=" * 50)
    logger.info(f"{'DRY RUN - Would have deleted' if dry_run else 'Deleted'}:")
    logger.info(f"  - {stats['analyses']} Firestore analyses")
    logger.info(f"  - {stats['videos']} videos from GCS")
    logger.info(f"  - {stats['replays']} replays from GCS")
    logger.info(f"  - {stats['thumbnails']} thumbnails from GCS")
    logger.info(f"  - {stats['audio_files']} audio files from GCS")

    if dry_run:
        logger.info("\nTo actually delete, run with --execute flag")


def main():
    parser = argparse.ArgumentParser(
        description="Delete all analyses from Firestore and GCS"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete (default is dry run)"
    )

    args = parser.parse_args()

    if args.execute:
        confirm = input("Are you sure you want to delete ALL analyses? (type 'yes' to confirm): ")
        if confirm.lower() != "yes":
            logger.info("Aborted.")
            sys.exit(0)

    cleanup_all(dry_run=not args.execute)


if __name__ == "__main__":
    main()
