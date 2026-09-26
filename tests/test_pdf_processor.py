from pathlib import Path
import fitz  # pymupdf
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import Asset, ContentChunk
from backend.processors.pdf_processor import process_pdf_asset

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        conn.exec_driver_sql("""
            CREATE VIRTUAL TABLE IF NOT EXISTS content_chunks_fts USING fts5(
                chunk_id UNINDEXED,
                asset_id UNINDEXED,
                text_content,
                filename
            );
        """)
        conn.commit()
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()

def test_process_pdf_asset(tmp_path: Path, test_db):
    pdf_path = tmp_path / "test_doc.pdf"
    
    # Create a 2-page test PDF
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((50, 50), "AssetLens digital asset management system for corporate assets and documents.")
    page2 = doc.new_page()
    page2.insert_text((50, 50), "Second page detailing multi-modal search architectures and vector indexing.")
    doc.save(str(pdf_path))
    doc.close()

    asset = Asset(
        path=str(pdf_path),
        filename=pdf_path.name,
        file_type="PDF",
        size_bytes=pdf_path.stat().st_size,
        file_hash="dummy_pdf_hash_123",
        mtime=pdf_path.stat().st_mtime,
        status="PENDING"
    )
    test_db.add(asset)
    test_db.commit()
    test_db.refresh(asset)

    chunks = process_pdf_asset(asset, test_db)

    assert len(chunks) >= 4  # 2 PDF_PAGE + 2 PDF_TEXT
    chunk_types = {c.chunk_type for c in chunks}
    assert "PDF_PAGE" in chunk_types
    assert "PDF_TEXT" in chunk_types
    assert asset.status == "INDEXED"

    # Verify FTS5 insertion
    fts_rows = test_db.execute(text("SELECT * FROM content_chunks_fts WHERE asset_id = :aid"), {"aid": asset.id}).fetchall()
    assert len(fts_rows) >= 2
