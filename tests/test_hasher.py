import hashlib
from pathlib import Path
import pytest
from backend.ingestion.hasher import compute_sha256

def test_compute_sha256(tmp_path: Path):
    test_file = tmp_path / "sample.txt"
    content = b"AssetLens multimodal AI DAM test content"
    test_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()
    computed_hash = compute_sha256(test_file)

    assert computed_hash == expected_hash

def test_compute_sha256_missing_file(tmp_path: Path):
    missing_file = tmp_path / "does_not_exist.bin"
    with pytest.raises(FileNotFoundError):
        compute_sha256(missing_file)
