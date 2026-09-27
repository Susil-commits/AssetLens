"""
Re-index script: marks all 163 missing files as PENDING and triggers full indexing.
Run this directly (outside the FastAPI server) from the project root.
"""
import sys
import logging
from pathlib import Path

# Setup logging so we see progress
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent  # scripts/ -> project root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.database import init_db, SessionLocal
from backend.ingestion.indexer import start_indexing, run_indexing_pipeline
from backend.config import settings
from backend.models import IndexRun, Asset

def check_pre_state(db):
    total = db.query(Asset).count()
    by_status = {}
    for status in ["INDEXED", "PENDING", "FAILED", "DUPLICATE", "UNSUPPORTED", "DISCOVERED", "PROCESSING"]:
        cnt = db.query(Asset).filter(Asset.status == status).count()
        if cnt:
            by_status[status] = cnt
    print(f"\nPre-run DB state: {total} total assets")
    for k, v in by_status.items():
        print(f"  {k}: {v}")

def check_disk_counts():
    media_dir = settings.MEDIA_DIR
    counts = {}
    for sub in ["images", "videos", "documents"]:
        d = media_dir / sub
        if d.exists():
            files = [f for f in d.iterdir() if f.is_file() and not f.name.startswith(".")]
            counts[sub] = len(files)
    total = sum(counts.values())
    print(f"\nFiles on disk: {counts} => Total: {total}")

if __name__ == "__main__":
    print("=" * 60)
    print("AssetLens Full Re-Index")
    print("=" * 60)

    init_db()
    db = SessionLocal()

    check_disk_counts()
    check_pre_state(db)

    media_dir = str(settings.MEDIA_DIR)
    print(f"\nTarget directory: {media_dir}")
    print("Starting indexing pipeline (runs in foreground for monitoring)...")
    print("=" * 60)

    db.close()

    # Run synchronously in main thread for full visibility
    import uuid
    from backend.database import SessionLocal
    from backend.models import IndexRun, utc_now

    db2 = SessionLocal()
    run_id = str(uuid.uuid4())
    run = IndexRun(
        id=run_id,
        folder_path=media_dir,
        status="RUNNING",
        started_at=utc_now()
    )
    db2.add(run)
    db2.commit()
    db2.close()

    # Run in foreground so we see all logs
    run_indexing_pipeline(run_id, media_dir)

    db3 = SessionLocal()
    run_obj = db3.query(IndexRun).filter(IndexRun.id == run_id).first()
    print("\n" + "=" * 60)
    print("INDEXING COMPLETE")
    print("=" * 60)
    if run_obj:
        print(f"  Status:     {run_obj.status}")
        print(f"  Total:      {run_obj.total_files}")
        print(f"  Indexed:    {run_obj.indexed_files}")
        print(f"  Skipped:    {run_obj.skipped_files}")
        print(f"  Duplicates: {run_obj.duplicate_files}")
        print(f"  Failed:     {run_obj.failed_files}")
        print(f"  Unsupported:{run_obj.unsupported_files}")
        print(f"  Started:    {run_obj.started_at}")
        print(f"  Completed:  {run_obj.completed_at}")
        if run_obj.error_summary:
            print(f"  Error:      {run_obj.error_summary}")

    # Post-run failed breakdown
    failed = db3.query(Asset).filter(Asset.status == "FAILED").all()
    if failed:
        print(f"\n--- FAILED ASSETS ({len(failed)}) ---")
        for a in failed:
            print(f"  [{a.file_type}] {a.filename} => {a.error_category}: {str(a.error_message)[:100]}")
    else:
        print("\n  No failed assets.")

    db3.close()
    print("\nDone.")
