import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.models import Asset
from backend.ingestion.hasher import compute_sha256

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv"}
PDF_EXTENSIONS = {".pdf"}

IGNORED_NAMES = {".ds_store", "thumbs.db", "desktop.ini"}

def classify_file(path: Union[str, Path]) -> str:
    ext = Path(path).suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return "IMAGE"
    if ext in VIDEO_EXTENSIONS:
        return "VIDEO"
    if ext in PDF_EXTENSIONS:
        return "PDF"
    return "UNSUPPORTED"

def should_ignore(path: Path) -> bool:
    name = path.name.lower()
    if name.startswith(".") or name.startswith("~$") or name in IGNORED_NAMES:
        return True
    return False

def scan_directory(folder_path: Union[str, Path], db: Session) -> Dict[str, Union[int, List[Asset]]]:
    """
    Recursively scans folder_path.
    Performs incremental check via (path, size, mtime).
    Performs content deduplication via SHA-256 hash.
    Sets status to:
      - 'DUPLICATE' if hash exists in DB on another file
      - 'UNSUPPORTED' if file type is unsupported
      - 'PENDING' if new or modified supported file
    """
    root = Path(folder_path).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Directory does not exist or is not a directory: {root}")

    total_scanned = 0
    unchanged_count = 0
    duplicate_count = 0
    pending_assets: List[Asset] = []
    unsupported_count = 0

    for current_root, dirs, files in os.walk(root):
        # Filter out hidden directories in-place
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for filename in files:
            file_path = (Path(current_root) / filename).resolve()
            if should_ignore(file_path):
                continue

            try:
                stat = file_path.stat()
            except (OSError, PermissionError):
                continue

            total_scanned += 1
            path_str = str(file_path)
            size_bytes = stat.st_size
            mtime = stat.st_mtime
            file_type = classify_file(file_path)

            # 1. Incremental Check: compare path, size, and mtime
            existing_asset = db.query(Asset).filter(Asset.path == path_str).first()
            if existing_asset is not None:
                # If path, size, and mtime match, file is unchanged
                if (existing_asset.size_bytes == size_bytes and 
                    abs(existing_asset.mtime - mtime) < 1e-3 and 
                    existing_asset.status in ("INDEXED", "DUPLICATE", "UNSUPPORTED")):
                    unchanged_count += 1
                    continue

            # 2. Compute SHA-256 for new or modified file
            try:
                file_hash = compute_sha256(file_path)
            except Exception as e:
                # File read error
                asset = existing_asset or Asset(path=path_str, filename=filename)
                asset.file_type = file_type
                asset.size_bytes = size_bytes
                asset.file_hash = "ERROR"
                asset.mtime = mtime
                asset.status = "FAILED"
                asset.error_category = "CORRUPT_FILE"
                asset.error_message = str(e)
                db.add(asset)
                db.commit()
                continue

            # 3. Deduplication Check: does this hash already exist in another asset?
            duplicate_match = db.query(Asset).filter(
                Asset.file_hash == file_hash,
                Asset.path != path_str
            ).first()

            target_status = "PENDING"
            error_cat = None
            error_msg = None

            if duplicate_match is not None:
                target_status = "DUPLICATE"
                duplicate_count += 1
            elif file_type == "UNSUPPORTED":
                target_status = "UNSUPPORTED"
                error_cat = "UNSUPPORTED_FORMAT"
                error_msg = f"Unsupported file extension: {file_path.suffix}"
                unsupported_count += 1

            if existing_asset is None:
                asset = Asset(
                    path=path_str,
                    filename=filename,
                    file_type=file_type,
                    size_bytes=size_bytes,
                    file_hash=file_hash,
                    mtime=mtime,
                    status=target_status,
                    error_category=error_cat,
                    error_message=error_msg,
                )
                db.add(asset)
            else:
                existing_asset.filename = filename
                existing_asset.file_type = file_type
                existing_asset.size_bytes = size_bytes
                existing_asset.file_hash = file_hash
                existing_asset.mtime = mtime
                existing_asset.status = target_status
                existing_asset.error_category = error_cat
                existing_asset.error_message = error_msg
                asset = existing_asset

            db.commit()
            db.refresh(asset)

            if target_status == "PENDING":
                pending_assets.append(asset)

    return {
        "total_scanned": total_scanned,
        "unchanged": unchanged_count,
        "duplicates": duplicate_count,
        "unsupported": unsupported_count,
        "pending_count": len(pending_assets),
        "pending_assets": pending_assets
    }
