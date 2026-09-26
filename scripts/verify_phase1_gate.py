import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import SessionLocal
from backend.models import Asset, ContentChunk
from backend.database_vectors import vector_db
from backend.search.ranking import execute_hybrid_search

def verify_phase1():
    print("=" * 70)
    print("PHASE 1 GATE VERIFICATION")
    print("=" * 70)

    db = SessionLocal()
    
    # 1. Check Asset Status
    assets = db.query(Asset).all()
    status_counts = {}
    type_counts = {}
    for a in assets:
        status_counts[a.status] = status_counts.get(a.status, 0) + 1
        type_counts[a.file_type] = type_counts.get(a.file_type, 0) + 1

    print("\n--- Asset Counts & Statuses ---")
    print(f"Total Assets in DB: {len(assets)}")
    print(f"By Status: {status_counts}")
    print(f"By Type:   {type_counts}")

    unindexed = [a for a in assets if a.status != "INDEXED"]
    if unindexed:
        print("\nWARNING: Some assets are not INDEXED:")
        for u in unindexed:
            print(f"  {u.filename} - Status: {u.status}, Error: {u.error_message}")
    else:
        print("ALL assets are in INDEXED status!")

    # 2. Check Chunks and Vector DB
    v_count = len(vector_db.visual_table.to_arrow())
    t_count = len(vector_db.text_table.to_arrow())
    c_count = db.query(ContentChunk).count()
    print("\n--- Embeddings & Chunks ---")
    print(f"SQLite Content Chunks: {c_count}")
    print(f"LanceDB Visual Embeddings: {v_count}")
    print(f"LanceDB Text Embeddings:   {t_count}")

    # 3. Test Assignment Example Queries
    test_queries = [
        "A woman standing with a cat",
        "Customer testimonial videos",
        "Brochures related to residential projects",
        "Images showing a modern living room",
        "Videos containing construction activity",
        "Documents mentioning 3 BHK apartments"
    ]

    print("\n--- Testing Assignment Example Queries ---")
    for q in test_queries:
        print(f"\nQuery: \"{q}\"")
        res = execute_hybrid_search(query=q, db=db, limit=3)
        results = res.get("results", [])
        if not results:
            print("  [NO RESULTS]")
            continue
        for idx, r in enumerate(results, 1):
            print(f"  #{idx} [{r['relevance_score']:.4f}] {r['filename']} ({r['file_type']})")
            print(f"      Matched: {r['matched_sources']} | Explanation: {r['explanation']}")

    db.close()
    print("\n" + "=" * 70)
    print("Gate 1 Verification Complete.")
    print("=" * 70)

if __name__ == "__main__":
    verify_phase1()
