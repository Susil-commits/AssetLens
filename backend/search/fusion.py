from typing import List, Dict, Any
from collections import defaultdict

RRF_K = 60.0
WEIGHT_VISUAL = 0.50
WEIGHT_TEXT = 0.35
WEIGHT_KEYWORD = 0.15

def build_match_explanation(sources: List[str], best_visual_score: float, best_text_score: float, snippet: str, page: int, ts: float) -> str:
    """Builds a factual, data-grounded explanation for why this item matched."""
    parts = []
    if "visual" in sources and best_visual_score > 0:
        conf = int(min(100, max(1, (best_visual_score + 0.15) * 100)))
        if ts is not None:
            parts.append(f"Visual scene matched at timestamp {int(ts)}s (confidence: {conf}%)")
        elif page is not None:
            parts.append(f"Visual page layout/diagram matched on page {page} (confidence: {conf}%)")
        else:
            parts.append(f"Visual scene matched prompt (confidence: {conf}%)")

    if "text" in sources and best_text_score > 0:
        if page is not None and snippet:
            clean_snip = snippet.replace("\n", " ").strip()[:90]
            parts.append(f"Text content matched on page {page}: \"{clean_snip}...\"")
        elif snippet:
            clean_snip = snippet.replace("\n", " ").strip()[:90]
            parts.append(f"Text content matched: \"{clean_snip}...\"")

    if "keyword" in sources:
        if snippet and "Filename" in snippet:
            parts.append(snippet)
        else:
            parts.append("Keyword matched in document text")

    if not parts:
        return "Matched search query criteria"
    return " | ".join(parts)

def fuse_and_rank_results(
    visual_hits: List[Dict[str, Any]],
    text_hits: List[Dict[str, Any]],
    keyword_hits: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Applies Reciprocal Rank Fusion (RRF) across visual, dense text, and keyword streams,
    aggregating by asset_id to produce unique, ranked asset matches with explanations.
    """
    asset_scores = defaultdict(float)
    asset_data = {}
    asset_sources = defaultdict(set)
    asset_best_visual = defaultdict(float)
    asset_best_text = defaultdict(float)
    asset_best_page = defaultdict(lambda: None)
    asset_best_timestamp = defaultdict(lambda: None)
    asset_best_snippet = defaultdict(lambda: None)

    # 1. Process Visual Stream (Asset-level best rank)
    seen_visual_aids = set()
    asset_visual_rank = 0
    for hit in visual_hits:
        aid = hit["asset_id"]
        asset_sources[aid].add("visual")
        if hit["score"] > asset_best_visual[aid]:
            asset_best_visual[aid] = hit["score"]
            if hit["timestamp_sec"] is not None:
                asset_best_timestamp[aid] = hit["timestamp_sec"]
            if hit["page_number"] is not None:
                asset_best_page[aid] = hit["page_number"]
        if aid not in asset_data:
            asset_data[aid] = hit

        if aid not in seen_visual_aids:
            seen_visual_aids.add(aid)
            asset_visual_rank += 1
            rrf = WEIGHT_VISUAL * (1.0 / (RRF_K + asset_visual_rank))
            asset_scores[aid] += rrf

    # 2. Process Text Stream (Asset-level best rank)
    seen_text_aids = set()
    asset_text_rank = 0
    for hit in text_hits:
        aid = hit["asset_id"]
        asset_sources[aid].add("text")
        if hit["score"] > asset_best_text[aid]:
            asset_best_text[aid] = hit["score"]
            if hit.get("text_snippet"):
                asset_best_snippet[aid] = hit["text_snippet"]
            if hit["page_number"] is not None:
                asset_best_page[aid] = hit["page_number"]
        if aid not in asset_data:
            asset_data[aid] = hit

        if aid not in seen_text_aids:
            seen_text_aids.add(aid)
            asset_text_rank += 1
            rrf = WEIGHT_TEXT * (1.0 / (RRF_K + asset_text_rank))
            asset_scores[aid] += rrf

    # 3. Process Keyword Stream (Asset-level best rank)
    seen_kw_aids = set()
    asset_kw_rank = 0
    for hit in keyword_hits:
        aid = hit["asset_id"]
        asset_sources[aid].add("keyword")
        if not asset_best_snippet[aid] and hit.get("text_snippet"):
            asset_best_snippet[aid] = hit["text_snippet"]
        if aid not in asset_data:
            asset_data[aid] = hit

        if aid not in seen_kw_aids:
            seen_kw_aids.add(aid)
            asset_kw_rank += 1
            rrf = WEIGHT_KEYWORD * (1.0 / (RRF_K + asset_kw_rank))
            asset_scores[aid] += rrf

    # 4. Form Consolidated Asset Results
    ranked_assets = []
    # Maximum theoretical RRF score for normalization
    max_rrf = (WEIGHT_VISUAL + WEIGHT_TEXT + WEIGHT_KEYWORD) / (RRF_K + 1)

    sorted_aids = sorted(asset_scores.keys(), key=lambda k: asset_scores[k], reverse=True)
    for aid in sorted_aids:
        raw_info = asset_data[aid]
        raw_rrf = asset_scores[aid]
        # Normalized relevance score between 0.0 and 1.0
        norm_score = round(min(1.0, raw_rrf / max_rrf * 1.5), 4)

        sources = sorted(list(asset_sources[aid]))
        vis_score = asset_best_visual[aid]
        txt_score = asset_best_text[aid]
        page = asset_best_page[aid]
        ts = asset_best_timestamp[aid]
        snippet = asset_best_snippet[aid]

        explanation = build_match_explanation(
            sources=sources,
            best_visual_score=vis_score,
            best_text_score=txt_score,
            snippet=snippet,
            page=page,
            ts=ts
        )

        ranked_assets.append({
            "asset_id": aid,
            "filename": raw_info.get("filename"),
            "path": raw_info.get("path"),
            "relevance_score": norm_score,
            "raw_rrf_score": raw_rrf,
            "matched_sources": sources,
            "matched_timestamp_sec": ts,
            "matched_page_number": page,
            "matched_snippet": snippet[:200] if snippet else None,
            "explanation": explanation
        })

    return ranked_assets
