from backend.database import init_db, engine
from sqlalchemy import text

def verify():
    init_db()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"))
        tables = [row[0] for row in result.fetchall()]
        print("Discovered tables:", tables)
        expected = ["assets", "content_chunks", "index_runs"]
        for exp in expected:
            assert exp in tables, f"Expected table {exp} missing!"
    print("Phase 0 DB Verification: SUCCESS! All expected tables exist in catalog.sqlite.")

if __name__ == "__main__":
    verify()
