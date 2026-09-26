import os
import uuid
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.config import settings
from backend.database import SessionLocal
from backend.models import Asset, IndexRun, utc_now
from backend.ingestion.scanner import scan_directory
from backend.processors.image_processor import process_image_asset
from backend.processors.pdf_processor import process_pdf_asset
from backend.processors.video_processor import process_video_asset

logger = logging.getLogger("assetlens.indexer")

# Global lock for single concurrent indexing run
_INDEX_LOCK = threading.Lock()
_ACTIVE_RUN_ID: Optional[str] = None

def classify_error(exc: Exception) -> str:
    """Categorizes an exception into a structured error category."""
    msg = str(exc).lower()
    name = type(exc).__name__.lower()

    if isinstance(exc, PermissionError) or "permission" in msg:
        return "PERMISSION_ERROR"
    if isinstance(exc, MemoryError) or "out of memory" in msg or "oom" in name:
        return "OOM"
    if isinstance(exc, TimeoutError) or "timeout" in msg:
        return "MODEL_TIMEOUT"
    if "corrupt" in msg or "cannot identify" in msg or "invalid" in msg or "not opened" in msg or "unidentified" in name:
        return "CORRUPT_FILE"
    if "unsupported" in msg:
        return "UNSUPPORTED_FORMAT"
    return "EXTRACTION_FAILED"

def run_indexing_pipeline(run_id: str, folder_path: str):
    """
    Background worker for scanning and indexing.
    Per-asset try/except guarantees that one bad file never halts indexing.
    """
    global _ACTIVE_RUN_ID
    db: Session = SessionLocal()
    try:
        run = db.query(IndexRun).filter(IndexRun.id == run_id).first()
        if not run:
            return

        target_dir = Path(folder_path).resolve()
        logger.info(f"Starting indexing run {run_id} on {target_dir}")

        # 1. Scan directory
        scan_res = scan_directory(target_dir, db)
        run.total_files = scan_res["total_scanned"]
        run.skipped_files = scan_res["unchanged"]
        run.duplicate_files = scan_res["duplicates"]
        run.unsupported_files = scan_res["unsupported"]
        db.commit()

        # 2. Query pending assets for this folder
        pending_assets = db.query(Asset).filter(
            Asset.status == "PENDING",
            Asset.path.startswith(str(target_dir))
        ).all()

        for asset in pending_assets:
            asset.status = "PROCESSING"
            db.commit()

            try:
                if asset.file_type == "IMAGE":
                    process_image_asset(asset, db)
                elif asset.file_type == "PDF":
                    process_pdf_asset(asset, db)
                elif asset.file_type == "VIDEO":
                    process_video_asset(asset, db)
                else:
                    asset.status = "UNSUPPORTED"
                    asset.error_category = "UNSUPPORTED_FORMAT"
                    db.commit()
                    run.unsupported_files += 1
                    continue

                run.indexed_files += 1
                db.commit()
                logger.info(f"Successfully indexed asset {asset.filename}")
            except Exception as e:
                logger.error(f"Failed to process asset {asset.filename}: {e}", exc_info=True)
                asset.status = "FAILED"
                asset.error_category = classify_error(e)
                asset.error_message = str(e)
                run.failed_files += 1
                db.commit()

        run.status = "COMPLETED"
        run.completed_at = utc_now()
        db.commit()
        logger.info(f"Indexing run {run_id} completed successfully.")
    except Exception as e:
        logger.critical(f"Indexing run {run_id} encountered fatal error: {e}", exc_info=True)
        if run:
            run.status = "FAILED"
            run.error_summary = str(e)
            run.completed_at = utc_now()
            db.commit()
    finally:
        _ACTIVE_RUN_ID = None
        db.close()

def start_indexing(folder_path: Optional[str] = None, db: Optional[Session] = None) -> Dict[str, Any]:
    """Starts asynchronous indexing run and returns run information."""
    global _ACTIVE_RUN_ID
    target = folder_path or str(settings.MEDIA_DIR)
    target_path = Path(target).resolve()
    if not target_path.exists():
        raise FileNotFoundError(f"Media folder does not exist: {target_path}")

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        run_id = str(uuid.uuid4())
        run = IndexRun(
            id=run_id,
            folder_path=str(target_path),
            status="RUNNING",
            started_at=utc_now()
        )
        db.add(run)
        db.commit()

        _ACTIVE_RUN_ID = run_id
        thread = threading.Thread(
            target=run_indexing_pipeline,
            args=(run_id, str(target_path)),
            daemon=True
        )
        thread.start()

        return {
            "run_id": run_id,
            "status": "RUNNING",
            "folder_path": str(target_path),
            "message": "Indexing started in background"
        }
    finally:
        if close_db:
            db.close()

def retry_failed_assets(db: Session) -> Dict[str, Any]:
    """Finds all FAILED assets and attempts re-processing."""
    failed_assets = db.query(Asset).filter(Asset.status == "FAILED").all()
    count = len(failed_assets)
    if count == 0:
        return {"retried_count": 0, "message": "No failed assets to retry"}

    retried_success = 0
    retried_failed = 0

    for asset in failed_assets:
        try:
            if asset.file_type == "IMAGE":
                process_image_asset(asset, db)
            elif asset.file_type == "PDF":
                process_pdf_asset(asset, db)
            elif asset.file_type == "VIDEO":
                process_video_asset(asset, db)
            retried_success += 1
        except Exception as e:
            asset.status = "FAILED"
            asset.error_category = classify_error(e)
            asset.error_message = str(e)
            db.commit()
            retried_failed += 1

    return {
        "total_attempted": count,
        "retried_success": retried_success,
        "retried_failed": retried_failed,
        "message": f"Retried {count} failed assets ({retried_success} succeeded, {retried_failed} still failing)"
    }
