import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
import lancedb
import pyarrow as pa
from backend.config import settings

class VectorDatabase:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(VectorDatabase, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.uri = str(settings.LANCEDB_URI)
        settings.ensure_directories()
        self.db = lancedb.connect(self.uri)
        self._init_tables()
        self._initialized = True

    def _init_tables(self):
        if hasattr(self.db, "list_tables"):
            table_names = set(self.db.list_tables())
        else:
            table_names = set(self.db.table_names())

        if "visual_embeddings" not in table_names:
            schema_visual = pa.schema([
                pa.field("id", pa.string()),
                pa.field("vector", pa.list_(pa.float32(), 768)),
                pa.field("asset_id", pa.string()),
                pa.field("chunk_type", pa.string()),
                pa.field("timestamp_sec", pa.float32()),
                pa.field("page_number", pa.int32()),
                pa.field("filename", pa.string()),
                pa.field("path", pa.string())
            ])
            self.visual_table = self.db.create_table("visual_embeddings", schema=schema_visual)
        else:
            self.visual_table = self.db.open_table("visual_embeddings")

        if "text_embeddings" not in table_names:
            schema_text = pa.schema([
                pa.field("id", pa.string()),
                pa.field("vector", pa.list_(pa.float32(), 384)),
                pa.field("asset_id", pa.string()),
                pa.field("chunk_type", pa.string()),
                pa.field("timestamp_sec", pa.float32()),
                pa.field("page_number", pa.int32()),
                pa.field("text_content", pa.string()),
                pa.field("filename", pa.string()),
                pa.field("path", pa.string())
            ])
            self.text_table = self.db.create_table("text_embeddings", schema=schema_text)
        else:
            self.text_table = self.db.open_table("text_embeddings")

    def add_visual_chunks(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return
        self.visual_table.add(chunks)

    def add_text_chunks(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return
        self.text_table.add(chunks)

    def delete_asset_chunks(self, asset_id: str):
        try:
            self.visual_table.delete(f"asset_id = '{asset_id}'")
        except Exception:
            pass
        try:
            self.text_table.delete(f"asset_id = '{asset_id}'")
        except Exception:
            pass

    def search_visual(self, vector: List[float], limit: int = 20) -> List[Dict[str, Any]]:
        if len(self.visual_table) == 0:
            return []
        results = self.visual_table.search(vector).metric("cosine").limit(limit).to_list()
        return results

    def search_text(self, vector: List[float], limit: int = 20) -> List[Dict[str, Any]]:
        if len(self.text_table) == 0:
            return []
        results = self.text_table.search(vector).metric("cosine").limit(limit).to_list()
        return results

vector_db = VectorDatabase()
