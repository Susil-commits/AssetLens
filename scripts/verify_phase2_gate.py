import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import SessionLocal
from backend.models import Asset, ContentChunk
from backend.processors.video_processor import process_video_asset
from backend.database_vectors import vector_db
from backend.search.ranking import execute_hybrid_search

def verify_phase2():
    print("=" * 70)
    print("PHASE 2 GATE VERIFICATION: SPEECH & TRANSCRIPT SEARCH")
    print("=" * 70)

    db = SessionLocal()

    # 1. Verify content_chunks in DB for customer testimonial video
    testimonial_asset = db.query(Asset).filter(Asset.filename == "customer_home_purchase_testimonial.mp4").first()
    assert testimonial_asset is not None, "Testimonial video asset not found in DB!"

    chunks = db.query(ContentChunk).filter(ContentChunk.asset_id == testimonial_asset.id).all()
    frame_chunks = [c for c in chunks if c.chunk_type == "VIDEO_FRAME"]
    transcript_chunks = [c for c in chunks if c.chunk_type == "VIDEO_TRANSCRIPT"]

    print("\n--- Direct Database Check (content_chunks table) ---")
    print(f"Asset ID: {testimonial_asset.id}")
    print(f"Total Chunks: {len(chunks)}")
    print(f"VIDEO_FRAME chunks: {len(frame_chunks)}")
    print(f"VIDEO_TRANSCRIPT chunks: {len(transcript_chunks)}")
    assert len(transcript_chunks) > 0, "No transcript chunks found in content_chunks table!"
    for c in transcript_chunks:
        print(f"  [{c.timestamp_sec:.2f}s]: {c.text_content}")

    # 2. Check search queries with spoken phrases and verify explanations
    spoken_queries = [
        "Customer testimonial videos",
        "People talking about their home purchase",
        "Priya Sharma home purchase story",
        "Olympic swimming pool for the kids"
    ]

    print("\n--- Spoken & Natural-Language Search Tests ---")
    for q in spoken_queries:
        print(f"\nQuery: \"{q}\"")
        res = execute_hybrid_search(query=q, db=db, limit=3)
        results = res.get("results", [])
        assert len(results) > 0, f"Query '{q}' returned no results!"
        top = results[0]
        print(f"  Top Match: {top['filename']} ({top['file_type']}) | Score: {top['relevance_score']:.4f}")
        print(f"  Matched Sources: {top['matched_sources']}")
        print(f"  Matched Timestamp: {top['matched_timestamp_sec']}s")
        print(f"  Explanation: {top['explanation']}")

    # 3. Test video with no audio / fallback behavior
    print("\n--- Testing Video Without Audio Track (Fallback to Visual Search) ---")
    silent_asset = db.query(Asset).filter(Asset.filename == "construction_worker_zone.mp4").first()
    assert silent_asset is not None, "Silent test asset not found"
    
    # Run a visual construction query
    res = execute_hybrid_search(query="Videos containing construction activity", db=db, limit=3)
    results = res.get("results", [])
    assert len(results) > 0, "Construction visual search returned no results!"
    top_video = next((r for r in results if r["file_type"] == "VIDEO"), None)
    assert top_video is not None, "Construction video not found in visual results!"
    print(f"  Matched visual video: {top_video['filename']}")
    print(f"  Explanation: {top_video['explanation']}")
    print("  Fallback to visual search succeeds with zero errors!")

    db.close()
    print("\n" + "=" * 70)
    print("Phase 2 Gate Verification Passed Successfully!")
    print("=" * 70)

if __name__ == "__main__":
    verify_phase2()
