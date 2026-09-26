import os
import uuid
from pathlib import Path
from typing import List, Dict, Any
import cv2
import numpy as np
from PIL import Image
from sqlalchemy.orm import Session
from backend.config import settings
from backend.models import Asset, ContentChunk, utc_now
from backend.ai.model_manager import model_manager
from backend.database_vectors import vector_db

def compute_sample_timestamps(duration_sec: float) -> List[float]:
    """Computes keyframe sample timestamps according to video duration."""
    if duration_sec <= 0:
        return [0.0]
    
    if duration_sec < 30:
        step = 2.0
    elif duration_sec <= 180:
        step = 4.0
    else:
        step = 10.0

    times = set()
    # First, middle, last
    times.add(0.0)
    times.add(round(duration_sec / 2.0, 2))
    times.add(max(0.0, round(duration_sec - 0.5, 2)))

    # Periodic intervals
    t = step
    while t < duration_sec:
        times.add(round(t, 2))
        t += step

    sorted_times = sorted(list(times))
    # Deduplicate timestamps closer than 0.8 seconds
    filtered = [sorted_times[0]]
    for cur in sorted_times[1:]:
        if cur - filtered[-1] >= 0.8:
            filtered.append(cur)
    return filtered

def is_frame_duplicate(frame1: np.ndarray, frame2: np.ndarray, threshold: float = 0.98) -> bool:
    """Checks if two consecutive frames are near-identical via histogram correlation."""
    if frame1 is None or frame2 is None:
        return False
    h1 = cv2.calcHist([frame1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    h2 = cv2.calcHist([frame2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    cv2.normalize(h1, h1)
    cv2.normalize(h2, h2)
    corr = cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL)
    return corr > threshold

def process_video_asset(asset: Asset, db: Session) -> List[ContentChunk]:
    """
    Extracts sampled keyframes, eliminates near-identical frames,
    generates cover and timestamped preview thumbnails, computes SigLIP embeddings,
    and indexes into SQLite content_chunks and LanceDB visual_embeddings.
    """
    file_path = Path(asset.path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Video file does not exist: {file_path}")

    # 1. Clean previous chunks for this asset
    vector_db.delete_asset_chunks(asset.id)
    db.query(ContentChunk).filter(ContentChunk.asset_id == asset.id).delete()

    cap = cv2.VideoCapture(str(file_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {file_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    duration_sec = total_frames / fps if total_frames > 0 else 10.0

    sample_timestamps = compute_sample_timestamps(duration_sec)
    created_chunks: List[ContentChunk] = []
    visual_records: List[Dict[str, Any]] = []

    last_frame_bgr = None
    middle_sec = duration_sec / 2.0
    cover_saved = False

    try:
        for idx, ts in enumerate(sample_timestamps):
            cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000.0)
            ret, frame_bgr = cap.read()
            if not ret or frame_bgr is None:
                continue

            # Check for near-identical duplicate frames
            if last_frame_bgr is not None and is_frame_duplicate(last_frame_bgr, frame_bgr):
                continue
            last_frame_bgr = frame_bgr

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)

            # Save cover thumbnail if near middle or first
            if not cover_saved or abs(ts - middle_sec) < 2.0:
                cover_path = settings.THUMBNAILS_DIR / f"{asset.id}.jpg"
                thumb_copy = pil_img.copy()
                thumb_copy.thumbnail((320, 320), Image.Resampling.LANCZOS)
                thumb_copy.save(cover_path, "JPEG", quality=85)
                cover_saved = True

            # Save timestamped preview thumbnail
            ts_thumb_path = settings.THUMBNAILS_DIR / f"{asset.id}_t{int(ts)}.jpg"
            preview_thumb = pil_img.copy()
            preview_thumb.thumbnail((480, 480), Image.Resampling.LANCZOS)
            preview_thumb.save(ts_thumb_path, "JPEG", quality=80)

            # Compute SigLIP embedding for this frame
            frame_vec = model_manager.encode_image(pil_img)
            chunk_id = str(uuid.uuid4())

            chunk = ContentChunk(
                id=chunk_id,
                asset_id=asset.id,
                chunk_type="VIDEO_FRAME",
                chunk_index=idx,
                timestamp_sec=ts,
                page_number=None,
                text_content=None,
                embedding_id=chunk_id,
                embedding_version=settings.EMBEDDING_VERSION,
                schema_version=settings.INDEX_SCHEMA_VERSION,
                created_at=utc_now()
            )
            db.add(chunk)
            created_chunks.append(chunk)

            visual_records.append({
                "id": chunk_id,
                "vector": frame_vec,
                "asset_id": asset.id,
                "chunk_type": "VIDEO_FRAME",
                "timestamp_sec": float(ts),
                "page_number": -1,
                "filename": asset.filename,
                "path": asset.path
            })
    finally:
        cap.release()

    # Bulk insert into LanceDB
    if visual_records:
        vector_db.add_visual_chunks(visual_records)

    asset.status = "INDEXED"
    asset.indexed_at = utc_now()
    asset.error_category = None
    asset.error_message = None
    db.commit()
    db.refresh(asset)

    return created_chunks
