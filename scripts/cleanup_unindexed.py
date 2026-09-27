"""
cleanup_unindexed.py
--------------------
Audit the AssetLens catalog and clean up media files that were NOT properly
indexed (statuses: FAILED, PENDING, UNSUPPORTED, DISCOVERED, PROCESSING).

What this script does:
  1. Prints a breakdown of all assets by status.
  2. For every asset whose status is in DELETE_STATUSES:
       - Deletes the physical file from disk (if it still exists).
       - Deletes the DB record (Asset row + cascaded ContentChunks).
  3. Prints a final summary.

Assets with status INDEXED or DUPLICATE are left completely untouched.

Run from the project root:
    python scripts/cleanup_unindexed.py          # dry-run (no changes)
    python scripts/cleanup_unindexed.py --delete  # actually delete
"""

import sys
import argparse
import logging
from pathlib import Path

# ── project root on sys.path ────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# Statuses that are considered "not properly indexed" and should be cleaned up.
DELETE_STATUSES = {"FAILED", "PENDING", "UNSUPPORTED", "DISCOVERED", "PROCESSING"}
# Statuses we consider "properly indexed" — never touched.
KEEP_STATUSES = {"INDEXED", "DUPLICATE"}


def parse_args():
    parser = argparse.ArgumentParser(description="Cleanup un-indexed AssetLens media.")
    parser.add_argument(
        "--delete",
        action="store_true",
        default=False,
        help="Actually delete files and DB records. Without this flag the script runs in DRY-RUN mode.",
    )
    return parser.parse_args()


def print_separator(char="=", width=60):
    print(char * width)


def audit_db(db):
    """Return a dict of {status: count} for all assets."""
    from backend.models import Asset

    all_statuses = list(DELETE_STATUSES | KEEP_STATUSES)
    counts = {}
    for status in sorted(all_statuses):
        cnt = db.query(Asset).filter(Asset.status == status).count()
        counts[status] = cnt
    # Also catch any unknown statuses
    total = db.query(Asset).count()
    accounted = sum(counts.values())
    if total != accounted:
        counts["OTHER"] = total - accounted
    return counts, total


def cleanup(db, dry_run: bool):
    from backend.models import Asset

    to_delete = (
        db.query(Asset)
        .filter(Asset.status.in_(list(DELETE_STATUSES)))
        .all()
    )

    deleted_files = 0
    missing_files = 0
    deleted_records = 0
    errors = 0

    for asset in to_delete:
        file_path = Path(asset.path)

        # ── physical file ────────────────────────────────────────────────
        if file_path.exists():
            if dry_run:
                log.info(f"[DRY-RUN] Would delete file: {file_path}")
            else:
                try:
                    file_path.unlink()
                    log.info(f"Deleted file: {file_path}")
                    deleted_files += 1
                except OSError as e:
                    log.error(f"Failed to delete {file_path}: {e}")
                    errors += 1
                    continue  # leave the DB record intact if file deletion failed
        else:
            log.warning(f"File not on disk (already gone): {file_path}")
            missing_files += 1

        # ── DB record (cascades to content_chunks) ───────────────────────
        if dry_run:
            log.info(f"[DRY-RUN] Would delete DB record: id={asset.id}  status={asset.status}  file={asset.filename}")
        else:
            try:
                db.delete(asset)
                deleted_records += 1
            except Exception as e:
                log.error(f"Failed to delete DB record {asset.id}: {e}")
                errors += 1

    if not dry_run:
        db.commit()

    return len(to_delete), deleted_files, missing_files, deleted_records, errors


def main():
    args = parse_args()
    dry_run = not args.delete

    from backend.database import init_db, SessionLocal

    init_db()
    db = SessionLocal()

    print_separator()
    print("AssetLens — Cleanup Un-Indexed Media")
    print("MODE:", "DRY-RUN (pass --delete to actually remove files)" if dry_run else "*** LIVE DELETE ***")
    print_separator()

    # ── 1. Audit ─────────────────────────────────────────────────────────────
    counts, total = audit_db(db)

    print(f"\nTotal assets in DB: {total}\n")
    print(f"{'Status':<20} {'Count':>8}  {'Action'}")
    print("-" * 50)
    for status, cnt in sorted(counts.items()):
        if cnt == 0:
            continue
        if status in KEEP_STATUSES:
            action = "KEEP (untouched)"
        else:
            action = "DELETE (file + DB record)"
        flag = "+" if status in KEEP_STATUSES else "-"
        print(f"  {flag} {status:<18} {cnt:>6}    {action}")

    properly_indexed = counts.get("INDEXED", 0)
    duplicates = counts.get("DUPLICATE", 0)
    to_remove = sum(v for k, v in counts.items() if k in DELETE_STATUSES)

    print("\n" + "-" * 50)
    print(f"  Properly indexed (INDEXED):   {properly_indexed}")
    print(f"  Kept as duplicates:           {duplicates}")
    print(f"  To be cleaned up:             {to_remove}")
    print("-" * 50)

    if to_remove == 0:
        print("\n  Nothing to clean up -- all assets are indexed or duplicate.")
        db.close()
        return

    # ── 2. Cleanup ───────────────────────────────────────────────────────────
    print()
    if dry_run:
        print(">>> DRY-RUN: listing what would be deleted <<<\n")
    else:
        print(">>> Deleting files and DB records... <<<\n")

    total_targeted, deleted_files, missing_files, deleted_records, errors = cleanup(db, dry_run)

    # ── 3. Summary ───────────────────────────────────────────────────────────
    print()
    print_separator()
    print("CLEANUP SUMMARY")
    print_separator()
    print(f"  Targeted assets:        {total_targeted}")
    if dry_run:
        print(f"  (Dry-run -- no changes made)")
    else:
        print(f"  Files deleted:          {deleted_files}")
        print(f"  Files already missing:  {missing_files}")
        print(f"  DB records deleted:     {deleted_records}")
        print(f"  Errors:                 {errors}")

    print()
    if dry_run:
        print("Re-run with --delete to actually perform the cleanup.")
    else:
        print("Cleanup complete.")

    db.close()


if __name__ == "__main__":
    main()
