import hashlib
from pathlib import Path
from typing import Union

CHUNK_SIZE = 1024 * 1024  # 1MB buffer

def compute_sha256(file_path: Union[str, Path]) -> str:
    """Computes SHA-256 hash of a file streaming in 1MB chunks."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)
    return hasher.hexdigest()
