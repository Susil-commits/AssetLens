from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import IndexRun
from backend.ingestion.indexer import start_indexing, retry_failed_assets

router = APIRouter(prefix="/api/index", tags=["indexing"])

class StartIndexRequest(BaseModel):
    folder_path: Optional[str] = None

@router.post("/start")
def api_start_indexing(
    req: Optional[StartIndexRequest] = None,
    db: Session = Depends(get_db)
):
    """Triggers asynchronous indexing on the media directory or custom folder."""
    path = req.folder_path if req else None
    try:
        return start_indexing(folder_path=path, db=db)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status")
def api_index_status(db: Session = Depends(get_db)):
    """Returns real-time status of the current or most recent indexing run."""
    latest_run = db.query(IndexRun).order_by(IndexRun.started_at.desc()).first()
    if not latest_run:
        return {
            "status": "IDLE",
            "message": "No indexing runs have been executed yet.",
            "total_files": 0,
            "indexed_files": 0,
            "progress_percent": 0.0
        }

    total = latest_run.total_files
    processed = (
        latest_run.indexed_files +
        latest_run.skipped_files +
        latest_run.failed_files +
        latest_run.duplicate_files +
        latest_run.unsupported_files
    )
    percent = round((processed / total * 100.0), 1) if total > 0 else (100.0 if latest_run.status == "COMPLETED" else 0.0)

    return {
        "run_id": latest_run.id,
        "status": latest_run.status,
        "folder_path": latest_run.folder_path,
        "total_files": latest_run.total_files,
        "indexed_files": latest_run.indexed_files,
        "skipped_files": latest_run.skipped_files,
        "failed_files": latest_run.failed_files,
        "duplicate_files": latest_run.duplicate_files,
        "unsupported_files": latest_run.unsupported_files,
        "progress_percent": min(100.0, percent),
        "started_at": latest_run.started_at.isoformat() if latest_run.started_at else None,
        "completed_at": latest_run.completed_at.isoformat() if latest_run.completed_at else None,
        "error_summary": latest_run.error_summary
    }

@router.get("/progress")
def api_index_progress(db: Session = Depends(get_db)):
    """Returns indexing progress and statistics (alias to /api/index/status)."""
    return api_index_status(db=db)

@router.post("/retry-failed")
def api_retry_failed(db: Session = Depends(get_db)):
    """Reprocesses only assets in FAILED status."""
    return retry_failed_assets(db)
