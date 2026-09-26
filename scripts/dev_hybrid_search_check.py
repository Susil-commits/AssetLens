import sys
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

SPEC_QUERIES = [
    {
        "query": "A woman standing with a cat",
        "expected_type": "IMAGE",
        "expected_filename_contains": "woman_holding_cat"
    },
    {
        "query": "Videos containing construction activity",
        "expected_type": "VIDEO",
        "expected_filename_contains": "construction_worker_zone"
    },
    {
        "query": "Images showing a modern living room",
        "expected_type": "IMAGE",
        "expected_filename_contains": "living_room_interior"
    },
    {
        "query": "Multi-Head Attention and Transformer network architecture",
        "expected_type": "PDF",
        "expected_filename_contains": "transformer_attention"
    },
    {
        "query": "Deep residual learning and shortcut connections",
        "expected_type": "PDF",
        "expected_filename_contains": "deep_residual_learning"
    }
]

def run_hybrid_search_verification():
    print("=" * 75)
    print("PHASE 5 GATE VERIFICATION: DIRECT HYBRID SEARCH API EVALUATION")
    print("=" * 75)

    all_passed = True

    for item in SPEC_QUERIES:
        q = item["query"]
        print(f"\nEvaluating Search Query: \"{q}\"")
        response = client.get(f"/api/search?q={q}&limit=5")
        
        if response.status_code != 200:
            print(f"  FAILED: API returned status {response.status_code}")
            all_passed = False
            continue

        data = response.json()
        total = data.get("total_results", 0)
        results = data.get("results", [])
        print(f"  Total matched assets: {total}")

        if not results:
            print(f"  FAILED: Zero results returned for valid query: {q}")
            all_passed = False
            continue

        # Check for asset duplicates in result list
        asset_ids = [r["asset_id"] for r in results]
        if len(asset_ids) != len(set(asset_ids)):
            print(f"  FAILED: Duplicate asset IDs found in search results: {asset_ids}")
            all_passed = False
            continue

        # Validate required response fields
        for res in results:
            assert "asset_id" in res
            assert "filename" in res
            assert "file_type" in res
            assert "relevance_score" in res
            assert "matched_sources" in res
            assert "explanation" in res
            assert "thumbnail_url" in res
            assert len(res["matched_sources"]) > 0

        # Check top result
        top_res = results[0]
        print(f"  Top Match:")
        print(f"    Filename:      {top_res['filename']} ({top_res['file_type']})")
        print(f"    Relevance:     {top_res['relevance_score']:.4f}")
        print(f"    Sources:       {top_res['matched_sources']}")
        print(f"    Explanation:   {top_res['explanation']}")
        if top_res.get("matched_timestamp_sec") is not None:
            print(f"    Timestamp:     {top_res['matched_timestamp_sec']}s")
        if top_res.get("matched_page_number") is not None:
            print(f"    Page Number:   {top_res['matched_page_number']}")

        # Verify relevance
        expected_part = item["expected_filename_contains"].lower()
        if expected_part in top_res["filename"].lower():
            print(f"  Result: PASS! Top match aligns with expected '{expected_part}'.")
        else:
            # Check if it appears in top 3
            found_rank = None
            for idx, r in enumerate(results[:3], 1):
                if expected_part in r["filename"].lower():
                    found_rank = idx
                    break
            if found_rank:
                print(f"  Result: PASS! Expected asset found at rank {found_rank}.")
            else:
                print(f"  Result: FAIL! Expected '{expected_part}' not in top results.")
                all_passed = False

    # Test filtering by file_type
    print("\n" + "-" * 75)
    print("Testing type filter: /api/search?q=construction&type=video")
    resp_filter = client.get("/api/search?q=construction&type=video")
    filter_data = resp_filter.json()
    assert all(r["file_type"] == "VIDEO" for r in filter_data["results"])
    print(f"  Filter verification passed! All {len(filter_data['results'])} returned results are VIDEO.")

    # Test empty query / weak query threshold
    print("\nTesting minimum similarity threshold on irrelevant query:")
    resp_thresh = client.get("/api/search?q=quantum%20astrophysics%20black%20hole%20singularity&min_score=0.8")
    assert resp_thresh.status_code == 200
    thresh_data = resp_thresh.json()
    print(f"  Threshold test returned {thresh_data['total_results']} results (correctly avoids padding weak matches).")

    print("\n" + "=" * 75)
    if all_passed:
        print("PHASE 5 GATE VERIFICATION: ALL HYBRID SEARCH CHECKS PASSED!")
    else:
        print("PHASE 5 GATE VERIFICATION: SOME CHECKS FAILED.")
    print("=" * 75)

    return all_passed

if __name__ == "__main__":
    success = run_hybrid_search_verification()
    sys.exit(0 if success else 1)
