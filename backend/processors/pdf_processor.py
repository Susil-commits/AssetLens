import io
import uuid
from pathlib import Path
from typing import List
import pymupdf
from PIL import Image
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.config import settings
from backend.models import Asset, ContentChunk, utc_now
from backend.ai.model_manager import model_manager
from backend.database_vectors import vector_db

def chunk_text_by_words(text_content: str, max_words: int = 500, overlap: int = 50) -> List[str]:
    """Splits long text into overlapping chunks of 300-600 words."""
    words = text_content.split()
    if len(words) <= max_words:
        return [text_content]
    
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += max_words - overlap
    return chunks

def process_pdf_asset(asset: Asset, db: Session) -> List[ContentChunk]:
    """
    Extracts text per page, chunks and embeds via dense text model,
    renders page images and embeds via SigLIP for visual PDF search,
    generates cover thumbnail, and indexes text in SQLite FTS5.
    """
    file_path = Path(asset.path)
    if not file_path.is_file():
        raise FileNotFoundError(f"PDF file does not exist: {file_path}")

    # 1. Clean previous chunks for this asset
    vector_db.delete_asset_chunks(asset.id)
    db.query(ContentChunk).filter(ContentChunk.asset_id == asset.id).delete()
    db.execute(
        text("DELETE FROM content_chunks_fts WHERE asset_id = :asset_id"),
        {"asset_id": asset.id}
    )

    created_chunks: List[ContentChunk] = []
    visual_records = []
    text_records = []

    doc = pymupdf.open(file_path)
    total_pages = len(doc)
    
    try:
        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc[page_idx]

            # A. Render Page Image for Visual Search & Preview
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("jpeg")
            page_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")

            # Save cover thumbnail (page 1)
            if page_idx == 0:
                thumb_path = settings.THUMBNAILS_DIR / f"{asset.id}.jpg"
                page_pil.thumbnail((320, 320), Image.Resampling.LANCZOS)
                page_pil.save(thumb_path, "JPEG", quality=85)

            # Save individual page preview
            page_preview_path = settings.THUMBNAILS_DIR / f"{asset.id}_p{page_num}.jpg"
            preview_copy = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            preview_copy.thumbnail((800, 800), Image.Resampling.LANCZOS)
            preview_copy.save(page_preview_path, "JPEG", quality=85)

            # Visual Embedding for Page
            page_visual_vec = model_manager.encode_image(page_pil)
            visual_chunk_id = str(uuid.uuid4())
            visual_chunk = ContentChunk(
                id=visual_chunk_id,
                asset_id=asset.id,
                chunk_type="PDF_PAGE",
                chunk_index=page_num,
                timestamp_sec=None,
                page_number=page_num,
                text_content=None,
                embedding_id=visual_chunk_id,
                embedding_version=settings.EMBEDDING_VERSION,
                schema_version=settings.INDEX_SCHEMA_VERSION,
                created_at=utc_now()
            )
            db.add(visual_chunk)
            created_chunks.append(visual_chunk)

            visual_records.append({
                "id": visual_chunk_id,
                "vector": page_visual_vec,
                "asset_id": asset.id,
                "chunk_type": "PDF_PAGE",
                "timestamp_sec": -1.0,
                "page_number": page_num,
                "filename": asset.filename,
                "path": asset.path
            })

            # B. Extract Page Text & Embed
            page_text = page.get_text("text").strip()
            if len(page_text) >= 15:
                sub_chunks = chunk_text_by_words(page_text)
                for sub_idx, chunk_str in enumerate(sub_chunks):
                    text_vec = model_manager.encode_text_dense(chunk_str)
                    text_chunk_id = str(uuid.uuid4())
                    
                    text_chunk = ContentChunk(
                        id=text_chunk_id,
                        asset_id=asset.id,
                        chunk_type="PDF_TEXT",
                        chunk_index=(page_num * 100) + sub_idx,
                        timestamp_sec=None,
                        page_number=page_num,
                        text_content=chunk_str,
                        embedding_id=text_chunk_id,
                        embedding_version=settings.EMBEDDING_VERSION,
                        schema_version=settings.INDEX_SCHEMA_VERSION,
                        created_at=utc_now()
                    )
                    db.add(text_chunk)
                    created_chunks.append(text_chunk)

                    text_records.append({
                        "id": text_chunk_id,
                        "vector": text_vec,
                        "asset_id": asset.id,
                        "chunk_type": "PDF_TEXT",
                        "timestamp_sec": -1.0,
                        "page_number": page_num,
                        "text_content": chunk_str,
                        "filename": asset.filename,
                        "path": asset.path
                    })

                    # Index in SQLite FTS5 for BM25 keyword matching
                    db.execute(
                        text("""
                            INSERT INTO content_chunks_fts(chunk_id, asset_id, text_content, filename)
                            VALUES (:chunk_id, :asset_id, :text_content, :filename)
                        """),
                        {
                            "chunk_id": text_chunk_id,
                            "asset_id": asset.id,
                            "text_content": chunk_str,
                            "filename": asset.filename
                        }
                    )
    finally:
        doc.close()

    # Bulk insert into LanceDB
    if visual_records:
        vector_db.add_visual_chunks(visual_records)
    if text_records:
        vector_db.add_text_chunks(text_records)

    asset.status = "INDEXED"
    asset.indexed_at = utc_now()
    asset.error_category = None
    asset.error_message = None
    db.commit()
    db.refresh(asset)

    return created_chunks
