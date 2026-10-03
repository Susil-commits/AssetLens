"""
remux_ts_videos.py
------------------
One-time migration: finds all VIDEO assets in the DB that are actually
MPEG-TS streams (disguised as .mp4), re-muxes them to seekable faststart
MP4 using FFmpeg stream-copy (no re-encoding, no quality loss), and writes
the remuxed path back into the DB so the media endpoint serves them.

Run once:
    .venv\\Scripts\\python.exe scripts\\remux_ts_videos.py
"""

import sys
import subprocess
from pathlib import Path

# ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.config import settings
from backend.database import SessionLocal
from backend.models import Asset
import imageio_ffmpeg

_MPEGTS_SYNC_BYTE = b"\x47"

def is_mpeg_ts(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(1) == _MPEGTS_SYNC_BYTE
    except OSError:
        return False

def remux(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        print(f"  [SKIP]    already remuxed: {dst.name}")
        return True
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        result = subprocess.run(
            [
                ffmpeg_exe, "-y",
                "-i", str(src),
                "-c", "copy",
                "-movflags", "+faststart",
                "-f", "mp4",
                str(dst),
            ],
            capture_output=True,
            timeout=300,
        )
        if result.returncode != 0:
            print(f"  [ERROR]   ffmpeg failed:\n{result.stderr.decode(errors='replace')[-600:]}")
            return False
        size_mb = dst.stat().st_size / 1024 / 1024
        print(f"  [OK]      {dst.name}  ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"  [ERROR]   {e}")
        return False

def main():
    remuxed_dir = settings.DERIVED_DIR / "remuxed"
    remuxed_dir.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        videos = db.query(Asset).filter(Asset.file_type == "VIDEO").all()
        print(f"Found {len(videos)} VIDEO assets.\n")

        done = skipped = failed = 0

        for asset in videos:
            src = Path(asset.path)
            if not src.is_file():
                print(f"  [MISSING] {asset.filename}")
                skipped += 1
                continue

            # Already remuxed in a previous run?
            if asset.error_category and asset.error_category.startswith("__remuxed__:"):
                rp = Path(asset.error_category.split("__remuxed__:", 1)[1])
                if rp.is_file():
                    print(f"  [ALREADY] {asset.filename}")
                    skipped += 1
                    continue

            if not is_mpeg_ts(src):
                print(f"  [MP4-OK]  {asset.filename}  (real MP4, no remux needed)")
                skipped += 1
                continue

            print(f"  [TS]      {asset.filename}  ({src.stat().st_size/1024/1024:.1f} MB)")
            dst = remuxed_dir / (src.stem + "__remuxed.mp4")

            if remux(src, dst):
                asset.error_category = f"__remuxed__:{dst}"
                db.commit()
                done += 1
            else:
                failed += 1

        print(f"\nDone.  remuxed={done}  skipped={skipped}  failed={failed}")
        print(f"Remuxed files are in: {remuxed_dir}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
