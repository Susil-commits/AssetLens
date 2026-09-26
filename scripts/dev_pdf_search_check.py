import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sqlalchemy.orm import Session
from backend.database import SessionLocal, init_db
from backend.models import Asset, ContentChunk
from backend.ingestion.scanner import scan_directory
from backend.processors.pdf_processor import process_pdf_asset
from backend.ai.model_manager import model_manager
from backend.database_vectors import vector_db

def run_pdf_search_check():
    init_db()
    db: Session = SessionLocal()
    docs_dir = Path("data/media/documents").resolve()

    print(f"Scanning PDF documents directory: {docs_dir}")
    scan_res = scan_directory(docs_dir, db)
    print(f"Scan complete: {scan_res['total_scanned']} total, {scan_res['pending_count']} pending.")

    # Process all pending PDF assets
    pending = db.query(Asset).filter(Asset.status == "PENDING", Asset.file_type == "PDF").all()
    print(f"Processing {len(pending)} PDF assets through PyMuPDF & dual embedders...")

    for i, asset in enumerate(pending, 1):
        print(f"[{i}/{len(pending)}] Indexing PDF: {asset.filename}...")
        chunks = process_pdf_asset(asset, db)
        print(f"  Generated {len(chunks)} chunks for {asset.filename}")

    indexed_count = db.query(Asset).filter(Asset.status == "INDEXED", Asset.file_type == "PDF").count()
    print(f"Total indexed PDFs in DB: {indexed_count}")

    print("\n" + "="*70)
    print("TEST 1: TEXT-BASED DENSE EMBEDDING RETRIEVAL")
    print("="*70)

    text_queries = [
        (
            "Documents mentioning 3 BHK apartments at Greenwood Heights Phase 2",
            "greenwood_heights_residential_brochure.pdf"
        ),
        (
            "Master floor plans and residential architecture booklet",
            "skyline_towers_floor_plans.pdf"
        ),
        (
            "Gated residential community and villa enclave brochure",
            "oakridge_sanctuary_community_brochure.pdf"
        )
    ]

    all_passed = True
    for query_text, expected_doc in text_queries:
        print(f"\nQuery (Text): '{query_text}'")
        text_vec = model_manager.encode_text_dense(query_text)
        results = vector_db.search_text(text_vec, limit=3)

        if not results:
            print("  Result: FAIL! No text results returned.")
            all_passed = False
            continue

        print("Top results:")
        for r, res in enumerate(results, 1):
            sim = 1.0 - res.get("_distance", 1.0)
            print(f"  {r}. {res['filename']} (Page {res.get('page_number')}, Similarity: {sim:.4f})")

        top_doc = results[0]["filename"]
        top_page = results[0].get("page_number")
        if top_doc == expected_doc:
            print(f"  Result: PASS! Top document '{top_doc}' (Page {top_page}) matched expected.")
        else:
            print(f"  Result: FAIL! Expected '{expected_doc}', got '{top_doc}'")
            all_passed = False

    print("\n" + "="*70)
    print("TEST 2: VISUAL PAGE RETRIEVAL (SigLIP over rendered PDF pages)")
    print("="*70)

    visual_queries = [
        (
            "Official brochure cover and residential project layout",
            "greenwood_heights_residential_brochure.pdf"
        ),
        (
            "Architectural floor plan schematic with room dimensions",
            "skyline_towers_floor_plans.pdf"
        )
    ]

    for query_vis, expected_doc in visual_queries:
        print(f"\nQuery (Visual): '{query_vis}'")
        vis_vec = model_manager.encode_text_for_visual_search(query_vis)
        # Search visual table filtered to PDF_PAGE
        results = vector_db.search_visual(vis_vec, limit=5)
        # Filter for PDF_PAGE chunks
        pdf_page_results = [r for r in results if r.get("chunk_type") == "PDF_PAGE"]

        if not pdf_page_results:
            print("  Result: FAIL! No visual PDF page results returned.")
            all_passed = False
            continue

        print("Top visual page results:")
        for r, res in enumerate(pdf_page_results[:3], 1):
            sim = 1.0 - res.get("_distance", 1.0)
            print(f"  {r}. {res['filename']} (Page {res.get('page_number')}, Similarity: {sim:.4f})")

        top_doc = pdf_page_results[0]["filename"]
        top_page = pdf_page_results[0].get("page_number")
        if top_doc == expected_doc:
            print(f"  Result: PASS! Top visual page is from '{top_doc}' (Page {top_page}).")
        else:
            print(f"  Result: FAIL! Expected '{expected_doc}', got '{top_doc}'")
            all_passed = False

    print("\n" + "="*70)
    if all_passed:
        print("PHASE 3 GATE VERIFICATION: ALL TEXT & VISUAL PDF QUERIES PASSED ACCURATELY!")
    else:
        print("PHASE 3 GATE VERIFICATION: FAILURES DETECTED.")
    print("="*70)

    db.close()
    return all_passed

if __name__ == "__main__":
    success = run_pdf_search_check()
    sys.exit(0 if success else 1)
