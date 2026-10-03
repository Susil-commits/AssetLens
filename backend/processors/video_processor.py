import os
import uuid
from pathlib import Path
from typing import List, Dict, Any
import cv2
import numpy as np
from PIL import Image
import logging
import subprocess
import imageio_ffmpeg
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.config import settings
from backend.models import Asset, ContentChunk, utc_now
from backend.ai.model_manager import model_manager
from backend.ai.transcription import transcriber
from backend.database_vectors import vector_db

logger = logging.getLogger("assetlens.video_processor")

_MPEGTS_SYNC_BYTE = b"\x47"

def _is_mpeg_ts(file_path: Path) -> bool:
    """Returns True if the file is an MPEG-TS stream (sync byte 0x47 at offset 0)."""
    try:
        with open(file_path, "rb") as f:
            return f.read(1) == _MPEGTS_SYNC_BYTE
    except OSError:
        return False

def _remux_to_mp4(src: Path, dst: Path) -> bool:
    """Re-muxes an MPEG-TS file to a seekable faststart MP4 using FFmpeg.
    Uses stream-copy (no re-encoding) — very fast, no quality loss.
    Returns True on success."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return True  # already done
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        result = subprocess.run(
            [
                ffmpeg_exe, "-y",
                "-i", str(src),
                "-c", "copy",          # stream copy — no re-encoding
                "-movflags", "+faststart",  # moov atom at front for instant seek
                "-f", "mp4",
                str(dst),
            ],
            capture_output=True,
            timeout=300,
        )
        if result.returncode != 0:
            logger.warning(
                f"FFmpeg re-mux failed for {src.name}: "
                f"{result.stderr.decode(errors='replace')[-400:]}"
            )
            return False
        logger.info(f"Re-muxed MPEG-TS → MP4 faststart: {dst.name}")
        return True
    except Exception as e:
        logger.warning(f"Re-mux error for {src.name}: {e}")
        return False

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

    For MPEG-TS files disguised as .mp4 (detected by sync byte 0x47), the file
    is re-muxed to a seekable faststart MP4 in derived/remuxed/ so the browser
    can seek to matched timestamps.
    """
    file_path = Path(asset.path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Video file does not exist: {file_path}")

    # Re-mux MPEG-TS streams to seekable MP4 so the browser can seek them.
    # The original file is never modified; the remux lives in derived/remuxed/.
    remuxed_dir = settings.DERIVED_DIR / "remuxed"
    remuxed_path = remuxed_dir / (file_path.stem + "__remuxed.mp4")
    source_for_cv = file_path

    if _is_mpeg_ts(file_path):
        if _remux_to_mp4(file_path, remuxed_path):
            source_for_cv = remuxed_path
            # Store remuxed path in asset so the media endpoint can serve it
            asset.error_message = None
            # Use a sentinel comment in error_category to track remux path
            # (reusing an existing nullable column rather than a schema change)
            asset.error_category = f"__remuxed__:{remuxed_path}"
        else:
            logger.warning(f"Re-mux failed for {file_path.name}; will use original (seek may not work).")

    vector_db.delete_asset_chunks(asset.id)
    db.query(ContentChunk).filter(ContentChunk.asset_id == asset.id).delete()
    try:
        db.execute(
            text("DELETE FROM content_chunks_fts WHERE asset_id = :asset_id"),
            {"asset_id": asset.id}
        )
    except Exception:
        pass

    cap = cv2.VideoCapture(str(source_for_cv))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {source_for_cv}")

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

    # Bulk insert visual chunks into LanceDB
    if visual_records:
        vector_db.add_visual_chunks(visual_records)

    # 2. Extract and index speech audio transcripts via faster-whisper
    text_records: List[Dict[str, Any]] = []
    fts_rows: List[Dict[str, Any]] = []   # Fix 4: collect for batch insert
    try:
        segments = transcriber.transcribe_video(file_path)
        for s_idx, seg in enumerate(segments):
            seg_text = seg.get("text", "").strip()
            seg_start = seg.get("start", 0.0)
            if not seg_text:
                continue

            text_vec = model_manager.encode_text_dense(seg_text)
            chunk_id = str(uuid.uuid4())

            chunk = ContentChunk(
                id=chunk_id,
                asset_id=asset.id,
                chunk_type="VIDEO_TRANSCRIPT",
                chunk_index=1000 + s_idx,
                timestamp_sec=seg_start,
                page_number=None,
                text_content=seg_text,
                embedding_id=chunk_id,
                embedding_version=settings.EMBEDDING_VERSION,
                schema_version=settings.INDEX_SCHEMA_VERSION,
                created_at=utc_now()
            )
            db.add(chunk)
            created_chunks.append(chunk)

            text_records.append({
                "id": chunk_id,
                "vector": text_vec,
                "asset_id": asset.id,
                "chunk_type": "VIDEO_TRANSCRIPT",
                "timestamp_sec": float(seg_start),
                "page_number": -1,
                "text_content": seg_text,
                "filename": asset.filename,
                "path": asset.path
            })

            # Fix 4: accumulate FTS5 rows instead of inserting one-by-one
            fts_rows.append({
                "chunk_id": chunk_id,
                "asset_id": asset.id,
                "text_content": seg_text,
                "filename": asset.filename,
            })

        # Fix 4: single batch insert for all transcript segments
        if fts_rows:
            try:
                db.execute(
                    text("""
                        INSERT INTO content_chunks_fts(chunk_id, asset_id, text_content, filename)
                        VALUES (:chunk_id, :asset_id, :text_content, :filename)
                    """),
                    fts_rows,
                )
            except Exception as fts_err:
                logger.warning(f"Failed to batch-insert transcript chunks into FTS: {fts_err}")

    except Exception as trans_err:
        logger.warning(f"Audio transcription encountered error on {asset.filename}: {trans_err}. Proceeding with visual frames only.")

    if text_records:
        vector_db.add_text_chunks(text_records)


    asset.status = "INDEXED"
    asset.indexed_at = utc_now()
    asset.error_category = None
    asset.error_message = None
    db.commit()
    db.refresh(asset)

    return created_chunks
