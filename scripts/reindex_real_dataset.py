import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sqlalchemy.orm import Session
from backend.database import SessionLocal, init_db
from backend.models import Asset, ContentChunk, IndexRun, utc_now
from backend.database_vectors import vector_db
from backend.ingestion.scanner import scan_directory
from backend.processors.image_processor import process_image_asset
from backend.processors.pdf_processor import process_pdf_asset
from backend.processors.video_processor import process_video_asset

def reindex_all():
    print("=" * 70)
    print("RE-INDEXING ALL REAL DATASET ASSETS CLEANLY")
    print("=" * 70)
    
    init_db()
    db: Session = SessionLocal()

    # 1. Purge test artifacts from SQLite
    print("Cleaning test artifacts from database...")
    media_root = str(Path("data/media").resolve()).lower()
    all_assets = db.query(Asset).all()
    for a in all_assets:
        resolved_path = str(Path(a.path).resolve()).lower()
        if not Path(a.path).exists() or not resolved_path.startswith(media_root) or "valid_photo" in a.filename or "corrupted_photo" in a.filename or "data_sheet" in a.filename:
            print(f"  Removing stale/artifact asset: {a.filename}")
            vector_db.delete_asset_chunks(a.id)
            db.query(ContentChunk).filter(ContentChunk.asset_id == a.id).delete()
            db.delete(a)
    
    # Clean index runs
    db.query(IndexRun).delete()
    db.commit()

    # 2. Reset LanceDB tables cleanly
    print("\nRe-initializing LanceDB tables...")
    try:
        vector_db.db.drop_table("visual_embeddings")
    except Exception:
        pass
    try:
        vector_db.db.drop_table("text_embeddings")
    except Exception:
        pass
    vector_db._init_tables()
    print("LanceDB tables initialized.")

    # 3. Clean FTS5 table
    print("Resetting FTS5 virtual table...")
    try:
        from sqlalchemy import text
        db.execute(text("DELETE FROM content_chunks_fts"))
        db.commit()
    except Exception as e:
        print(f"FTS5 delete warning: {e}")

    # 4. Clean content_chunks table
    db.query(ContentChunk).delete()
    db.commit()

    # 5. Scan data/media to register all real files
    print("\nScanning data/media directory...")
    scan_res = scan_directory(Path("data/media").resolve(), db)
    print(f"Scan complete: {scan_res['total_scanned']} files scanned, {scan_res['pending_count']} pending.")

    # Mark all real assets as PENDING to force fresh indexing
    db.query(Asset).update({Asset.status: "PENDING"})
    db.commit()

    pending_assets = db.query(Asset).filter(Asset.status == "PENDING").all()
    print(f"\nProcessing {len(pending_assets)} real assets:")

    # Images first
    images = [a for a in pending_assets if a.file_type == "IMAGE"]
    for i, asset in enumerate(images, 1):
        print(f"[{i}/{len(images)}] Indexing Image: {asset.filename}")
        process_image_asset(asset, db)

    # PDFs next
    pdfs = [a for a in pending_assets if a.file_type == "PDF"]
    for i, asset in enumerate(pdfs, 1):
        print(f"[{i}/{len(pdfs)}] Indexing PDF: {asset.filename}")
        chunks = process_pdf_asset(asset, db)
        print(f"  -> Generated {len(chunks)} chunks")

    # Videos next
    videos = [a for a in pending_assets if a.file_type == "VIDEO"]
    for i, asset in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] Indexing Video: {asset.filename}")
        chunks = process_video_asset(asset, db)
        print(f"  -> Extracted {len(chunks)} keyframe chunks")

    db.close()

    # Verification
    print("\n" + "=" * 70)
    print("VERIFYING LANCEDB & SQLITE STATE AFTER RE-INDEXING")
    print("=" * 70)
    v_count = len(vector_db.visual_table.to_arrow())
    t_count = len(vector_db.text_table.to_arrow())
    print(f"Total Visual Embeddings in LanceDB: {v_count}")
    print(f"Total Text Embeddings in LanceDB:   {t_count}")

    db_check = SessionLocal()
    total_indexed = db_check.query(Asset).filter(Asset.status == "INDEXED").count()
    total_chunks = db_check.query(ContentChunk).count()
    print(f"Total INDEXED Assets in SQLite:     {total_indexed}")
    print(f"Total Content Chunks in SQLite:     {total_chunks}")
    db_check.close()
    print("\nRe-indexing completed successfully!")

if __name__ == "__main__":
    reindex_all()
