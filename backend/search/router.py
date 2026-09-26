import mimetypes
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Asset
from backend.search.ranking import execute_hybrid_search

router = APIRouter(prefix="/api", tags=["search"])

@router.get("/search")
def search_assets(
    q: str = Query(..., description="Natural language search query"),
    type: str = Query("all", description="Filter by file type: all, image, video, pdf"),
    min_score: Optional[float] = Query(None, description="Minimum relevance threshold"),
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
    db: Session = Depends(get_db)
):
    """
    Multimodal natural language search over indexed images, videos, and documents.
    Fuses SigLIP visual search, dense text embeddings, and SQLite FTS5 BM25 keyword matching.
    """
    return execute_hybrid_search(
        query=q,
        db=db,
        file_type=type,
        min_score=min_score,
        limit=limit
    )

@router.get("/media/{asset_id}")
def serve_media_file(asset_id: str, db: Session = Depends(get_db)):
    """Serves the original media file for in-browser preview."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    file_path = Path(asset.path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found on disk: {file_path}")

    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    return FileResponse(
        path=str(file_path),
        media_type=mime_type,
        filename=asset.filename
    )

@router.get("/assets")
def list_assets(
    status: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Lists indexed and discovered assets with metadata."""
    query = db.query(Asset)
    if status:
        query = query.filter(Asset.status == status.upper())
    if type and type.lower() != "all":
        query = query.filter(Asset.file_type == type.upper())
    
    total = query.count()
    assets = query.order_by(Asset.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "assets": [
            {
                "id": a.id,
                "filename": a.filename,
                "file_type": a.file_type,
                "size_bytes": a.size_bytes,
                "status": a.status,
                "path": a.path,
                "error_category": a.error_category,
                "error_message": a.error_message,
                "indexed_at": a.indexed_at.isoformat() if a.indexed_at else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "thumbnail_url": f"/api/thumbnails/{a.id}.jpg"
            }
            for a in assets
        ]
    }
