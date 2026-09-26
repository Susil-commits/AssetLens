import re
from typing import Optional, Set

IMAGE_INTENT = {
    "image", "images", "photo", "photos", "picture", "pictures", "photograph", "photographs"
}
VIDEO_INTENT = {
    "video", "videos", "clip", "clips", "footage", "recording", "recordings"
}
PDF_INTENT = {
    "brochure", "brochures", "pdf", "pdfs", "document", "documents", "paper", "papers", "report", "reports"
}

QUERY_STOPWORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "showing", "containing", "related", "find", "search", "show", "get", "all",
    "some", "any", "that", "this", "from", "by", "about"
}

ALL_FILTER_WORDS = IMAGE_INTENT | VIDEO_INTENT | PDF_INTENT | QUERY_STOPWORDS

def detect_media_intent(query: str) -> Optional[str]:
    """Detects whether user prompt explicitly specifies a target media modality."""
    tokens = set(re.findall(r"\b[a-zA-Z]+\b", query.lower()))
    if tokens & IMAGE_INTENT:
        return "IMAGE"
    if tokens & VIDEO_INTENT:
        return "VIDEO"
    if tokens & PDF_INTENT:
        return "PDF"
    return None

def extract_content_keywords(query: str) -> str:
    """Extracts meaningful semantic content keywords by removing stop and modality words."""
    words = re.findall(r"\b[a-zA-Z0-9_-]+\b", query.lower())
    content_words = [w for w in words if w not in ALL_FILTER_WORDS and len(w) > 1]
    
    # If all words were filtered out, fallback to raw words
    if not content_words:
        content_words = [w for w in words if len(w) > 2]
    
    if not content_words:
        return ""
    return " OR ".join(f'"{w}"' for w in content_words)
