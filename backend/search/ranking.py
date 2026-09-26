from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from backend.config import settings
from backend.models import Asset
from backend.search.visual_search import search_visual
from backend.search.text_search import search_text
from backend.search.keyword_search import search_keyword
from backend.search.fusion import fuse_and_rank_results
from backend.search.query_parser import detect_media_intent

def execute_hybrid_search(
    query: str,
    db: Session,
    file_type: str = "all",
    min_score: Optional[float] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Executes end-to-end hybrid retrieval:
    1. Multimodal visual search (SigLIP)
    2. Dense text retrieval (SentenceTransformers)
    3. Full-text keyword search (SQLite FTS5)
    4. RRF rank fusion & thresholding
    5. Parent asset metadata enrichment & deduplication
    """
    clean_q = query.strip()
    if not clean_q:
        return {"query": query, "total_results": 0, "filter_type": file_type, "results": []}

    threshold = min_score if min_score is not None else settings.SIMILARITY_THRESHOLD
    media_intent = detect_media_intent(clean_q) if file_type.lower() == "all" else None

    # 1. Fetch retrieval streams
    vis_hits = search_visual(clean_q, file_type_filter=file_type, limit=limit * 2)
    txt_hits = search_text(clean_q, file_type_filter=file_type, limit=limit * 2)
    kw_hits = search_keyword(clean_q, db, file_type_filter=file_type, limit=limit * 2)

    # 2. Fuse rankings via RRF
    fused_candidates = fuse_and_rank_results(vis_hits, txt_hits, kw_hits)

    # 3. Enrich with parent Asset details from SQLite
    enriched_results = []
    for item in fused_candidates:
        aid = item["asset_id"]
        asset = db.query(Asset).filter(Asset.id == aid).first()
        if not asset or asset.status != "INDEXED":
            continue

        score = item["relevance_score"]
        if media_intent:
            if asset.file_type == media_intent:
                score = round(min(1.0, score * 1.3 + 0.1), 4)
            else:
                score = round(score * 0.65, 4)

        if score < threshold:
            continue

        # Determine best thumbnail URL
        ts = item.get("matched_timestamp_sec")
        page = item.get("matched_page_number")
        thumb_name = f"{aid}.jpg"

        if ts is not None:
            candidate_ts = settings.THUMBNAILS_DIR / f"{aid}_t{int(ts)}.jpg"
            if candidate_ts.exists():
                thumb_name = candidate_ts.name
        elif page is not None:
            candidate_p = settings.THUMBNAILS_DIR / f"{aid}_p{page}.jpg"
            if candidate_p.exists():
                thumb_name = candidate_p.name

        enriched_results.append({
            "asset_id": asset.id,
            "filename": asset.filename,
            "file_type": asset.file_type,
            "path": asset.path,
            "size_bytes": asset.size_bytes,
            "relevance_score": score,
            "matched_sources": item["matched_sources"],
            "matched_timestamp_sec": ts,
            "matched_page_number": page,
            "matched_snippet": item.get("matched_snippet"),
            "explanation": item["explanation"],
            "thumbnail_url": f"/api/thumbnails/{thumb_name}",
            "preview_url": f"/api/media/{asset.id}"
        })

    # Sort final results by score descending
    enriched_results.sort(key=lambda x: x["relevance_score"], reverse=True)
    final_results = enriched_results[:limit]

    return {
        "query": query,
        "total_results": len(final_results),
        "filter_type": file_type,
        "results": final_results
    }
