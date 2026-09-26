import sys
from pathlib import Path
from sqlalchemy.orm import Session
from backend.database import SessionLocal, init_db
from backend.models import Asset
from backend.ingestion.scanner import scan_directory
from backend.processors.video_processor import process_video_asset
from backend.ai.model_manager import model_manager
from backend.database_vectors import vector_db

def run_video_search_check():
    init_db()
    db: Session = SessionLocal()
    video_dir = Path("data/media/videos").resolve()

    print(f"Scanning video directory: {video_dir}")
    scan_res = scan_directory(video_dir, db)
    print(f"Scan complete: {scan_res['total_scanned']} total, {scan_res['pending_count']} pending.")

    # Process all pending video assets
    pending = db.query(Asset).filter(Asset.status == "PENDING", Asset.file_type == "VIDEO").all()
    print(f"Processing {len(pending)} video assets through OpenCV & SigLIP...")

    for i, asset in enumerate(pending, 1):
        print(f"[{i}/{len(pending)}] Indexing video: {asset.filename}...")
        chunks = process_video_asset(asset, db)
        print(f"  Generated {len(chunks)} sampled keyframes for {asset.filename}")

    indexed_count = db.query(Asset).filter(Asset.status == "INDEXED", Asset.file_type == "VIDEO").count()
    print(f"Total indexed videos in DB: {indexed_count}")

    test_queries = [
        (
            "Construction activity with workers wearing safety gear in work zone",
            "construction_worker_zone.mp4"
        ),
        (
            "People and pedestrians walking outdoors on sidewalk or street",
            "people_walking_outdoors.mp4"
        )
    ]

    all_passed = True
    print("\n" + "="*70)
    print("RUNNING NATURAL LANGUAGE VISUAL QUERIES AGAINST VIDEO KEYFRAMES")
    print("="*70)

    for query_text, expected_video in test_queries:
        print(f"\nQuery: '{query_text}'")
        vis_vec = model_manager.encode_text_for_visual_search(query_text)
        results = vector_db.search_visual(vis_vec, limit=5)
        video_results = [r for r in results if r.get("chunk_type") == "VIDEO_FRAME"]

        if not video_results:
            print("  Result: FAIL! No video frames returned.")
            all_passed = False
            continue

        print("Top video keyframe matches:")
        for r, res in enumerate(video_results[:3], 1):
            sim = 1.0 - res.get("_distance", 1.0)
            print(f"  {r}. {res['filename']} at timestamp {res.get('timestamp_sec')}s (Similarity: {sim:.4f})")

        top_video = video_results[0]["filename"]
        top_ts = video_results[0].get("timestamp_sec")
        if top_video == expected_video:
            print(f"  Result: PASS! Top video match is '{top_video}' at timestamp {top_ts}s.")
        else:
            print(f"  Result: FAIL! Expected '{expected_video}', got '{top_video}'")
            all_passed = False

    print("\n" + "="*70)
    if all_passed:
        print("PHASE 4 GATE VERIFICATION: VIDEO RETRIEVAL WITH TIMESTAMPS PASSED ACCURATELY!")
    else:
        print("PHASE 4 GATE VERIFICATION: FAILURES DETECTED.")
    print("="*70)

    db.close()
    return all_passed

if __name__ == "__main__":
    success = run_video_search_check()
    sys.exit(0 if success else 1)
