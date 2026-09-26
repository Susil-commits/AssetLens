import time
from pathlib import Path
from PIL import Image
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import Asset, IndexRun
from backend.ingestion.indexer import run_indexing_pipeline, retry_failed_assets

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()

def test_corrupt_file_isolation_and_retry(tmp_path: Path, monkeypatch):
    # 1. Create a valid image
    good_img = tmp_path / "valid_photo.jpg"
    img = Image.new("RGB", (64, 64), color=(0, 255, 0))
    img.save(good_img)

    # 2. Create an unsupported file
    unsupported_file = tmp_path / "data_sheet.xyz"
    unsupported_file.write_bytes(b"some unknown format data")

    # 3. Create a corrupted image file
    corrupt_img = tmp_path / "corrupted_photo.jpg"
    corrupt_img.write_bytes(b"NOT_A_VALID_JPEG_HEADER_CORRUPTED_BYTES")

    # Setup DB session
    from backend.database import SessionLocal, init_db
    init_db()
    db = SessionLocal()

    run = IndexRun(
        id="test_reliability_run_1",
        folder_path=str(tmp_path),
        status="RUNNING"
    )
    db.add(run)
    db.commit()

    # Run the pipeline synchronously for deterministic testing
    run_indexing_pipeline(run.id, str(tmp_path))

    db.refresh(run)
    assert run.status == "COMPLETED"
    assert run.failed_files == 1
    assert run.unsupported_files == 1
    assert run.indexed_files == 1

    # Check the assets in DB
    valid_asset = db.query(Asset).filter(Asset.path == str(good_img.resolve())).first()
    assert valid_asset is not None
    assert valid_asset.status == "INDEXED"

    unsupported_asset = db.query(Asset).filter(Asset.path == str(unsupported_file.resolve())).first()
    assert unsupported_asset is not None
    assert unsupported_asset.status == "UNSUPPORTED"
    assert unsupported_asset.error_category == "UNSUPPORTED_FORMAT"

    corrupt_asset = db.query(Asset).filter(Asset.path == str(corrupt_img.resolve())).first()
    assert corrupt_asset is not None
    assert corrupt_asset.status == "FAILED"
    assert corrupt_asset.error_category == "CORRUPT_FILE"

    # Now "fix" the corrupt file on disk
    img_fixed = Image.new("RGB", (64, 64), color=(0, 0, 255))
    img_fixed.save(corrupt_img)

    # Call retry_failed_assets: it should only touch the failed asset
    retry_res = retry_failed_assets(db)
    assert retry_res["total_attempted"] == 1
    assert retry_res["retried_success"] == 1

    db.refresh(corrupt_asset)
    assert corrupt_asset.status == "INDEXED"
    assert corrupt_asset.error_category is None

    db.close()
