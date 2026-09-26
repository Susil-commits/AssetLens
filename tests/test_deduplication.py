from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import Asset
from backend.ingestion.scanner import scan_directory

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()

def test_deduplication_exact_copy(tmp_path: Path, test_db):
    content = b"Exact identical image binary content"
    folder_a = tmp_path / "folder_a"
    folder_b = tmp_path / "folder_b"
    folder_a.mkdir()
    folder_b.mkdir()

    file1 = folder_a / "image_original.png"
    file2 = folder_b / "image_copy.png"

    file1.write_bytes(content)
    file2.write_bytes(content)

    result = scan_directory(tmp_path, test_db)
    assert result["total_scanned"] == 2
    assert result["pending_count"] == 1
    assert result["duplicates"] == 1

    assets = test_db.query(Asset).all()
    statuses = {a.status for a in assets}
    assert "PENDING" in statuses
    assert "DUPLICATE" in statuses
