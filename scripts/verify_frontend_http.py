import httpx

def test_frontend_serving():
    client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=60.0)
    
    # 1. Root index.html
    r = client.get("/")
    assert r.status_code == 200
    assert '<div id="root"></div>' in r.text
    print("Frontend HTML: OK (200, contains #root)")

    # 2. Search API
    r_search = client.get("/api/search?q=living%20room")
    assert r_search.status_code == 200
    data = r_search.json()
    assert "results" in data
    print(f"Search API: OK (matched {data['total_results']} items)")

    # 3. Status API
    r_status = client.get("/api/index/status")
    assert r_status.status_code == 200
    print("Index Status API: OK")

    # 4. Assets API
    r_assets = client.get("/api/assets?limit=5")
    assert r_assets.status_code == 200
    print(f"Assets Catalog API: OK (total {r_assets.json()['total']} assets)")

    print("ALL FRONTEND HTTP & API ROUTES VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_frontend_serving()
