from pathlib import Path
import cv2
import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import Asset, ContentChunk
from backend.processors.video_processor import process_video_asset

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()

def test_process_video_asset(tmp_path: Path, test_db):
    video_path = tmp_path / "sample_test_video.mp4"
    
    # Create a 3-second test video with varying frames
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_path), fourcc, 10.0, (128, 128))
    for i in range(30):
        # Frame with changing color
        frame = np.full((128, 128, 3), (i * 8, 100, 200), dtype=np.uint8)
        out.write(frame)
    out.release()

    asset = Asset(
        path=str(video_path),
        filename=video_path.name,
        file_type="VIDEO",
        size_bytes=video_path.stat().st_size,
        file_hash="dummy_video_hash_456",
        mtime=video_path.stat().st_mtime,
        status="PENDING"
    )
    test_db.add(asset)
    test_db.commit()
    test_db.refresh(asset)

    chunks = process_video_asset(asset, test_db)

    assert len(chunks) >= 1
    assert all(c.chunk_type == "VIDEO_FRAME" for c in chunks)
    assert all(c.timestamp_sec is not None for c in chunks)
    assert asset.status == "INDEXED"

    # Cleanup vector_db test chunks
    from backend.database_vectors import vector_db
    vector_db.delete_asset_chunks(asset.id)

def test_process_video_asset_with_transcription(tmp_path: Path, test_db, monkeypatch):
    from backend.ai.transcription import transcriber
    from backend.database_vectors import vector_db

    video_path = tmp_path / "video_with_speech.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_path), fourcc, 10.0, (128, 128))
    for i in range(20):
        frame = np.full((128, 128, 3), (50, 100, i * 10), dtype=np.uint8)
        out.write(frame)
    out.release()

    # Mock transcriber to return predictable speech segments
    monkeypatch.setattr(
        transcriber,
        "transcribe_video",
        lambda p: [{"start": 1.5, "end": 4.0, "text": "Customer testimonial test phrase"}]
    )

    asset = Asset(
        path=str(video_path),
        filename=video_path.name,
        file_type="VIDEO",
        size_bytes=video_path.stat().st_size,
        file_hash="dummy_video_hash_speech_789",
        mtime=video_path.stat().st_mtime,
        status="PENDING"
    )
    test_db.add(asset)
    test_db.commit()
    test_db.refresh(asset)

    chunks = process_video_asset(asset, test_db)

    frame_chunks = [c for c in chunks if c.chunk_type == "VIDEO_FRAME"]
    transcript_chunks = [c for c in chunks if c.chunk_type == "VIDEO_TRANSCRIPT"]

    assert len(frame_chunks) >= 1
    assert len(transcript_chunks) == 1
    assert transcript_chunks[0].text_content == "Customer testimonial test phrase"
    assert transcript_chunks[0].timestamp_sec == 1.5
    assert asset.status == "INDEXED"

    vector_db.delete_asset_chunks(asset.id)

def test_process_video_transcription_fallback_on_error(tmp_path: Path, test_db, monkeypatch):
    from backend.ai.transcription import transcriber
    from backend.database_vectors import vector_db

    video_path = tmp_path / "video_failing_speech.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_path), fourcc, 10.0, (128, 128))
    for i in range(20):
        frame = np.full((128, 128, 3), (80, 80, 80), dtype=np.uint8)
        out.write(frame)
    out.release()

    # Simulate Whisper error / audio corruption
    def mock_failing_transcribe(p):
        raise RuntimeError("Simulated Whisper OOM / corrupt audio stream")
    monkeypatch.setattr(transcriber, "transcribe_video", mock_failing_transcribe)

    asset = Asset(
        path=str(video_path),
        filename=video_path.name,
        file_type="VIDEO",
        size_bytes=video_path.stat().st_size,
        file_hash="dummy_video_hash_fail_999",
        mtime=video_path.stat().st_mtime,
        status="PENDING"
    )
    test_db.add(asset)
    test_db.commit()
    test_db.refresh(asset)

    # Should not crash — visual frames are indexed as fallback
    chunks = process_video_asset(asset, test_db)

    assert len(chunks) >= 1
    assert all(c.chunk_type == "VIDEO_FRAME" for c in chunks)
    assert asset.status == "INDEXED"
    assert asset.error_category is None

    vector_db.delete_asset_chunks(asset.id)

