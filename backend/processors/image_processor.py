import os
import uuid
from pathlib import Path
from PIL import Image
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.config import settings
from backend.models import Asset, ContentChunk, utc_now
from backend.ai.model_manager import model_manager
from backend.database_vectors import vector_db

THUMBNAIL_SIZE = (320, 320)

def generate_image_thumbnail(image_path: Path, output_path: Path) -> Path:
    """Creates a high quality aspect-ratio-preserved thumbnail."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path) as img:
        img_rgb = img.convert("RGB")
        img_rgb.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        img_rgb.save(output_path, "JPEG", quality=85, optimize=True)
    return output_path

def process_image_asset(asset: Asset, db: Session) -> ContentChunk:
    """
    Extracts image metadata, generates a thumbnail, computes a SigLIP embedding,
    persists records to SQLite content_chunks and LanceDB visual_embeddings.
    """
    file_path = Path(asset.path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Image file does not exist: {file_path}")

    # 1. Clean previous chunks for this asset if any
    vector_db.delete_asset_chunks(asset.id)
    db.query(ContentChunk).filter(ContentChunk.asset_id == asset.id).delete()
    try:
        db.execute(
            text("DELETE FROM content_chunks_fts WHERE asset_id = :asset_id"),
            {"asset_id": asset.id}
        )
    except Exception:
        pass

    # 2. Thumbnail generation
    thumb_path = settings.THUMBNAILS_DIR / f"{asset.id}.jpg"
    generate_image_thumbnail(file_path, thumb_path)

    # 3. Compute SigLIP embedding
    embedding = model_manager.encode_image(file_path)

    # 4. Create ContentChunk in SQLite
    chunk_id = str(uuid.uuid4())
    chunk = ContentChunk(
        id=chunk_id,
        asset_id=asset.id,
        chunk_type="IMAGE",
        chunk_index=0,
        timestamp_sec=None,
        page_number=None,
        text_content=None,
        embedding_id=chunk_id,
        embedding_version=settings.EMBEDDING_VERSION,
        schema_version=settings.INDEX_SCHEMA_VERSION,
        created_at=utc_now()
    )
    db.add(chunk)

    # 5. Add to LanceDB
    vector_db.add_visual_chunks([{
        "id": chunk_id,
        "vector": embedding,
        "asset_id": asset.id,
        "chunk_type": "IMAGE",
        "timestamp_sec": -1.0,
        "page_number": -1,
        "filename": asset.filename,
        "path": asset.path
    }])

    # 6. Index filename in FTS5 for keyword search (e.g. "kitchen", "nature", "real_estate")
    stem = Path(asset.filename).stem.replace("_", " ").replace("-", " ")
    try:
        db.execute(
            text("""
                INSERT INTO content_chunks_fts(chunk_id, asset_id, text_content, filename)
                VALUES (:chunk_id, :asset_id, :text_content, :filename)
            """),
            {
                "chunk_id": chunk_id,
                "asset_id": asset.id,
                "text_content": stem,
                "filename": asset.filename
            }
        )
    except Exception:
        pass

    # 7. Update Asset status
    asset.status = "INDEXED"
    asset.indexed_at = utc_now()
    asset.error_category = None
    asset.error_message = None
    db.commit()
    db.refresh(asset)

    return chunk
