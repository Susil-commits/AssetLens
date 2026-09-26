from typing import List, Dict, Any, Optional
from backend.ai.model_manager import model_manager
from backend.database_vectors import vector_db

def search_visual(query: str, file_type_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Encodes query into SigLIP space and searches visual embeddings."""
    query_vec = model_manager.encode_text_for_visual_search(query)
    raw_results = vector_db.search_visual(query_vec, limit=limit * 2)

    hits = []
    for r in raw_results:
        chunk_type = r.get("chunk_type", "")
        # Filter by file type if specified
        if file_type_filter and file_type_filter.upper() != "ALL":
            target = file_type_filter.upper()
            if target == "IMAGE" and chunk_type != "IMAGE":
                continue
            if target == "VIDEO" and chunk_type != "VIDEO_FRAME":
                continue
            if target == "PDF" and chunk_type != "PDF_PAGE":
                continue

        # LanceDB distance to cosine similarity
        distance = float(r.get("_distance", 1.0))
        similarity = max(0.0, 1.0 - distance)

        hits.append({
            "chunk_id": r.get("id"),
            "asset_id": r.get("asset_id"),
            "chunk_type": chunk_type,
            "score": similarity,
            "timestamp_sec": r.get("timestamp_sec") if r.get("timestamp_sec", -1.0) >= 0 else None,
            "page_number": r.get("page_number") if r.get("page_number", -1) > 0 else None,
            "filename": r.get("filename"),
            "path": r.get("path"),
            "source": "visual"
        })
        if len(hits) >= limit:
            break

    return hits
