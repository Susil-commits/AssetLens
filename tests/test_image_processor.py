from pathlib import Path
from PIL import Image
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import Asset, ContentChunk
from backend.processors.image_processor import process_image_asset
from backend.database_vectors import vector_db

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()

def test_process_image_asset(tmp_path: Path, test_db):
    test_img = tmp_path / "sample_test_image.png"
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(test_img)

    asset = Asset(
        path=str(test_img),
        filename=test_img.name,
        file_type="IMAGE",
        size_bytes=test_img.stat().st_size,
        file_hash="dummy_hash_test_image",
        mtime=test_img.stat().st_mtime,
        status="PENDING"
    )
    test_db.add(asset)
    test_db.commit()
    test_db.refresh(asset)

    chunk = process_image_asset(asset, test_db)

    assert chunk is not None
    assert chunk.chunk_type == "IMAGE"
    assert asset.status == "INDEXED"
    assert asset.indexed_at is not None

    # Check that chunk is in DB
    db_chunks = test_db.query(ContentChunk).filter(ContentChunk.asset_id == asset.id).all()
    assert len(db_chunks) == 1
