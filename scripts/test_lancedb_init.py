import lancedb
import pyarrow as pa
from pathlib import Path
import numpy as np

def test_lancedb():
    db_path = Path("data/db/lancedb")
    db_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(db_path))

    schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), 768)),
        pa.field("asset_id", pa.string()),
        pa.field("chunk_type", pa.string()),
        pa.field("timestamp_sec", pa.float32()),
        pa.field("page_number", pa.int32()),
        pa.field("filename", pa.string()),
        pa.field("path", pa.string())
    ])

    tbl = db.create_table("visual_embeddings", schema=schema, mode="overwrite")
    
    # Insert a dummy record
    dummy_vec = np.random.randn(768).astype(np.float32)
    dummy_vec /= np.linalg.norm(dummy_vec)
    
    tbl.add([{
        "id": "chunk_1",
        "vector": dummy_vec.tolist(),
        "asset_id": "asset_1",
        "chunk_type": "IMAGE",
        "timestamp_sec": -1.0,
        "page_number": -1,
        "filename": "sample.jpg",
        "path": "/data/media/sample.jpg"
    }])

    # Run vector search
    query_vec = dummy_vec.tolist()
    results = tbl.search(query_vec).limit(5).to_list()
    assert len(results) == 1
    assert results[0]["id"] == "chunk_1"
    print("LanceDB visual_embeddings table initialized and search verified successfully!")

if __name__ == "__main__":
    test_lancedb()
