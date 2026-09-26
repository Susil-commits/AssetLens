import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    ForeignKey,
    Index
)
from sqlalchemy.orm import relationship
from backend.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    path = Column(String, unique=True, nullable=False, index=True)
    filename = Column(String, nullable=False, index=True)
    file_type = Column(String(20), nullable=False, index=True)  # IMAGE, VIDEO, PDF, UNSUPPORTED
    size_bytes = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    mtime = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="DISCOVERED", index=True)
    # DISCOVERED, PENDING, PROCESSING, INDEXED, DUPLICATE, FAILED, UNSUPPORTED
    error_message = Column(Text, nullable=True)
    error_category = Column(String(50), nullable=True)  # CORRUPT_FILE, UNSUPPORTED_FORMAT, OOM, MODEL_TIMEOUT, EXTRACTION_FAILED, PERMISSION_ERROR
    indexed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    chunks = relationship("ContentChunk", back_populates="asset", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_assets_status_type", "status", "file_type"),
        Index("idx_assets_hash", "file_hash"),
    )

class ContentChunk(Base):
    __tablename__ = "content_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    asset_id = Column(String(36), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_type = Column(String(30), nullable=False, index=True)  # IMAGE, PDF_TEXT, PDF_PAGE, PDF_OCR, VIDEO_FRAME, VIDEO_TRANSCRIPT
    chunk_index = Column(Integer, default=0, nullable=False)
    timestamp_sec = Column(Float, nullable=True)
    page_number = Column(Integer, nullable=True)
    text_content = Column(Text, nullable=True)
    embedding_id = Column(String(64), nullable=True, index=True)
    embedding_version = Column(String(30), default="v1.0", nullable=False)
    schema_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    asset = relationship("Asset", back_populates="chunks")

    __table_args__ = (
        Index("idx_chunks_asset_type", "asset_id", "chunk_type"),
    )

class IndexRun(Base):
    __tablename__ = "index_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    folder_path = Column(String, nullable=False)
    status = Column(String(20), default="RUNNING", nullable=False, index=True)  # RUNNING, COMPLETED, FAILED, CANCELLED
    total_files = Column(Integer, default=0, nullable=False)
    indexed_files = Column(Integer, default=0, nullable=False)
    skipped_files = Column(Integer, default=0, nullable=False)
    failed_files = Column(Integer, default=0, nullable=False)
    duplicate_files = Column(Integer, default=0, nullable=False)
    unsupported_files = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_summary = Column(Text, nullable=True)
