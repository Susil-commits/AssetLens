import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_search_api_basic():
    response = client.get("/api/search?q=living%20room&type=image")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_results" in data
    assert data["filter_type"] == "image"

def test_search_no_duplicates():
    response = client.get("/api/search?q=attention%20model")
    assert response.status_code == 200
    results = response.json().get("results", [])
    asset_ids = [r["asset_id"] for r in results]
    assert len(asset_ids) == len(set(asset_ids))

def test_search_empty_query():
    response = client.get("/api/search?q=")
    assert response.status_code == 200
    assert response.json()["total_results"] == 0

def test_list_assets_api():
    response = client.get("/api/assets?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "assets" in data
    assert "total" in data
