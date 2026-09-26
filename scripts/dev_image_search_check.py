import sys
from pathlib import Path
from sqlalchemy.orm import Session
from backend.database import SessionLocal, init_db
from backend.models import Asset
from backend.ingestion.scanner import scan_directory
from backend.processors.image_processor import process_image_asset
from backend.ai.model_manager import model_manager
from backend.database_vectors import vector_db

def run_image_search_check():
    init_db()
    db: Session = SessionLocal()
    media_dir = Path("data/media/images").resolve()

    print(f"Scanning directory: {media_dir}")
    scan_res = scan_directory(media_dir, db)
    print(f"Scan complete: {scan_res['total_scanned']} total, {scan_res['pending_count']} pending.")

    # Process all pending image assets
    pending = db.query(Asset).filter(Asset.status == "PENDING", Asset.file_type == "IMAGE").all()
    print(f"Processing {len(pending)} image assets through SigLIP...")

    for i, asset in enumerate(pending, 1):
        print(f"[{i}/{len(pending)}] Indexing {asset.filename}...")
        process_image_asset(asset, db)

    indexed_count = db.query(Asset).filter(Asset.status == "INDEXED", Asset.file_type == "IMAGE").count()
    print(f"Total indexed images in DB: {indexed_count}")

    # Plain-English test queries
    test_queries = [
        ("A cute pet or furry animal", ["woman_holding_cat.jpg", "dog_playing_park.jpg"]),
        ("A high speed sports automobile", ["sports_car_red.jpg"]),
        ("A modern living room with couch and furniture", ["living_room_interior.jpg"]),
        ("Hot morning beverage with foam art", ["coffee_latte_art.jpg"]),
        ("Heavy machinery and construction building site", ["construction_site_crane.jpg"])
    ]

    all_passed = True
    print("\n" + "="*70)
    print("RUNNING NATURAL LANGUAGE VISUAL QUERIES AGAINST LANCEDB")
    print("="*70)

    for query_text, expected_candidates in test_queries:
        print(f"\nQuery: '{query_text}'")
        query_vec = model_manager.encode_text_for_visual_search(query_text)
        results = vector_db.search_visual(query_vec, limit=3)

        top_match = results[0]["filename"] if results else None
        top_score = results[0]["_distance"] if results else None
        # In LanceDB cosine metric: distance = 1 - cosine_similarity, so lower distance is better match

        print(f"Top 3 Results:")
        for rank, res in enumerate(results, 1):
            sim = 1.0 - res.get("_distance", 1.0)
            print(f"  {rank}. {res['filename']} (Similarity: {sim:.4f}, Distance: {res.get('_distance', 0):.4f})")

        is_match = any(top_match == cand for cand in expected_candidates)
        if is_match:
            print(f"  Result: PASS! Top result '{top_match}' is visually correct.")
        else:
            print(f"  Result: FAIL! Expected one of {expected_candidates}, got '{top_match}'")
            all_passed = False

    print("\n" + "="*70)
    if all_passed:
        print("PHASE 2 GATE VERIFICATION: ALL 5 QUERIES PASSED WITH ACCURATE VISUAL MATCHES!")
    else:
        print("PHASE 2 GATE VERIFICATION: SOME QUERIES FAILED.")
    print("="*70)

    db.close()
    return all_passed

if __name__ == "__main__":
    success = run_image_search_check()
    sys.exit(0 if success else 1)
