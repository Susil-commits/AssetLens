from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import Asset
from backend.ingestion.scanner import classify_file, scan_directory

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()

def test_classify_file():
    assert classify_file("photo.jpg") == "IMAGE"
    assert classify_file("photo.PNG") == "IMAGE"
    assert classify_file("clip.mp4") == "VIDEO"
    assert classify_file("movie.MKV") == "VIDEO"
    assert classify_file("document.pdf") == "PDF"
    assert classify_file("document.PDF") == "PDF"
    assert classify_file("spreadsheet.xlsx") == "UNSUPPORTED"
    assert classify_file("archive.zip") == "UNSUPPORTED"

def test_scan_directory_and_incremental_skip(tmp_path: Path, test_db):
    # Setup test files
    img = tmp_path / "test1.jpg"
    img.write_bytes(b"dummy image content 1")
    doc = tmp_path / "test2.pdf"
    doc.write_bytes(b"dummy pdf content 2")
    unsupported = tmp_path / "notes.txt"
    unsupported.write_bytes(b"dummy notes")

    # First scan
    result1 = scan_directory(tmp_path, test_db)
    assert result1["total_scanned"] == 3
    assert result1["unchanged"] == 0
    assert result1["pending_count"] == 2
    assert result1["unsupported"] == 1

    # Simulate that pending assets are indexed
    for asset in test_db.query(Asset).filter(Asset.status == "PENDING").all():
        asset.status = "INDEXED"
    test_db.commit()

    # Second scan: should skip unchanged files completely
    result2 = scan_directory(tmp_path, test_db)
    assert result2["total_scanned"] == 3
    assert result2["unchanged"] == 3
    assert result2["pending_count"] == 0
