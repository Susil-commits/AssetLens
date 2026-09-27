import re
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.models import Asset, ContentChunk
from backend.search.query_parser import extract_content_keywords, ALL_FILTER_WORDS

logger = logging.getLogger("assetlens.keyword_search")

def search_keyword(query: str, db: Session, file_type_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Performs full-text keyword search via SQLite FTS5 table and filename matching."""
    clean_q = extract_content_keywords(query)
    hits = []
    seen_chunk_ids = set()

    # 1. FTS5 Search over indexed text content
    if clean_q:
        try:
            sql = text("""
                SELECT chunk_id, asset_id, text_content, filename, bm25(content_chunks_fts) as rank
                FROM content_chunks_fts
                WHERE content_chunks_fts MATCH :q
                ORDER BY rank ASC
                LIMIT :lim
            """)
            rows = db.execute(sql, {"q": clean_q, "lim": limit}).fetchall()
            for row in rows:
                chunk_id, asset_id, text_content, filename, rank = row
                # Normalize BM25 score (negative in SQLite FTS5, lower is better)
                score = 1.0 / (1.0 + abs(float(rank)))
                seen_chunk_ids.add(chunk_id)

                # Look up chunk details
                chunk = db.query(ContentChunk).filter(ContentChunk.id == chunk_id).first()
                asset = db.query(Asset).filter(Asset.id == asset_id).first()
                if not asset:
                    continue

                if file_type_filter and file_type_filter.upper() != "ALL":
                    if asset.file_type != file_type_filter.upper():
                        continue

                hits.append({
                    "chunk_id": chunk_id,
                    "asset_id": asset_id,
                    "chunk_type": chunk.chunk_type if chunk else "TEXT",
                    "score": score,
                    "timestamp_sec": chunk.timestamp_sec if chunk else None,
                    "page_number": chunk.page_number if chunk else None,
                    "text_snippet": text_content[:200] if text_content else None,
                    "filename": filename,
                    "path": asset.path,
                    "source": "keyword"
                })
        except Exception as fts_err:
            logger.warning(f"FTS5 keyword search failed for query '{clean_q}': {fts_err}")

    # 2. Filename substring matching
    words = [w.lower() for w in re.findall(r"\b[a-zA-Z0-9]+\b", query) if len(w) > 2 and w.lower() not in ALL_FILTER_WORDS]
    for w in words:
        matching_assets = db.query(Asset).filter(
            Asset.filename.ilike(f"%{w}%"),
            Asset.status == "INDEXED"
        ).all()
        for asset in matching_assets:
            if file_type_filter and file_type_filter.upper() != "ALL":
                if asset.file_type != file_type_filter.upper():
                    continue

            # Check if this asset already has a keyword hit
            if any(h["asset_id"] == asset.id for h in hits):
                continue

            hits.append({
                "chunk_id": f"fn_{asset.id}",
                "asset_id": asset.id,
                "chunk_type": asset.file_type,
                "score": 0.60,
                "timestamp_sec": None,
                "page_number": None,
                "text_snippet": f"Filename match for keyword '{w}'",
                "filename": asset.filename,
                "path": asset.path,
                "source": "keyword"
            })

    return hits[:limit]
