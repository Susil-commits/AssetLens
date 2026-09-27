import mimetypes
import re
import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse, Response
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Asset
from backend.search.ranking import execute_hybrid_search

CHUNK_SIZE = 1024 * 64  # 64 KB streaming chunks


def _stream_with_range(file_path: Path, request: Request, mime_type: str, filename: str) -> Response:
    """Fix 2: Serve a file with HTTP Range (byte-range) support for seekable video playback.

    Returns 206 Partial Content when a Range header is present, or a full 200 response
    that advertises Accept-Ranges so the browser knows it can seek later.
    """
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    headers_base = {
        "Accept-Ranges": "bytes",
        "Content-Disposition": f'inline; filename="{filename}"',
    }

    if range_header:
        match = re.match(r"bytes=(\d*)-(\d*)", range_header)
        if match:
            start = int(match.group(1)) if match.group(1) else 0
            end = int(match.group(2)) if match.group(2) else file_size - 1
            end = min(end, file_size - 1)
            length = end - start + 1

            def _iter_range(start: int, length: int):
                with open(file_path, "rb") as f:
                    f.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk = f.read(min(CHUNK_SIZE, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk

            return StreamingResponse(
                _iter_range(start, length),
                status_code=206,
                media_type=mime_type,
                headers={
                    **headers_base,
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Content-Length": str(length),
                },
            )

    # No Range header — serve full file with Accept-Ranges advertised
    return FileResponse(
        path=str(file_path),
        media_type=mime_type,
        filename=filename,
        headers=headers_base,
    )

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
def serve_media_file(asset_id: str, request: Request, db: Session = Depends(get_db)):
    """Streams the original media file with HTTP Range support for seekable video playback."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    file_path = Path(asset.path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found on disk: {file_path}")

    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    return _stream_with_range(file_path, request, mime_type, asset.filename)

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

@router.get("/assets/{asset_id}")
def get_asset_detail(asset_id: str, db: Session = Depends(get_db)):
    """Retrieves full metadata and chunk breakdown for a specific asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    chunks = [
        {
            "id": c.id,
            "chunk_type": c.chunk_type,
            "chunk_index": c.chunk_index,
            "timestamp_sec": c.timestamp_sec,
            "page_number": c.page_number,
            "snippet": c.text_content[:150] if c.text_content else None
        }
        for c in asset.chunks
    ]

    return {
        "id": asset.id,
        "filename": asset.filename,
        "file_type": asset.file_type,
        "size_bytes": asset.size_bytes,
        "status": asset.status,
        "path": asset.path,
        "file_hash": asset.file_hash,
        "mtime": asset.mtime,
        "error_category": asset.error_category,
        "error_message": asset.error_message,
        "indexed_at": asset.indexed_at.isoformat() if asset.indexed_at else None,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "thumbnail_url": f"/api/thumbnails/{asset.id}.jpg",
        "preview_url": f"/api/media/{asset.id}",
        "chunk_count": len(chunks),
        "chunks": chunks
    }

@router.get("/assets/{asset_id}/preview")
def preview_asset_media(asset_id: str, request: Request, db: Session = Depends(get_db)):
    """Serves the original media file for preview with Range support (alias to /api/media/{asset_id})."""
    return serve_media_file(asset_id=asset_id, request=request, db=db)
