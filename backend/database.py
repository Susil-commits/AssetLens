import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

DATABASE_URL = f"sqlite:///{settings.DB_PATH.as_posix()}"

# SQLite specific connect_args for multithreading and WAL mode
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    settings.ensure_directories()
    # Enable WAL mode for high concurrency
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
        conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
        conn.commit()

    from backend import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Initialize FTS5 table for keyword search
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
