import httpx
from pathlib import Path

SAMPLE_PDFS = [
    {
        "filename": "transformer_attention_paper.pdf",
        "url": "https://arxiv.org/pdf/1706.03762.pdf",
        "description": "Attention Is All You Need research paper"
    },
    {
        "filename": "residential_building_guidelines.pdf",
        "url": "https://www.hud.gov/sites/dfiles/OCHCO/documents/49001c13HSGH.pdf",
        "description": "Residential Building and Housing Guidelines"
    },
    {
        "filename": "renewable_energy_annual_report.pdf",
        "url": "https://www.nrel.gov/docs/fy21osti/77650.pdf",
        "description": "Renewable Energy and Solar Research Technical Report"
    }
]

def download_pdfs():
    out_dir = Path("data/media/documents")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    client = httpx.Client(timeout=60.0, follow_redirects=True, headers=headers)

    for item in SAMPLE_PDFS:
        dest = out_dir / item["filename"]
        if dest.exists() and dest.stat().st_size > 5000:
            print(f"Already exists: {item['filename']} ({dest.stat().st_size:,} bytes)")
            continue

        print(f"Downloading {item['filename']} from {item['url']}...")
        try:
            resp = client.get(item["url"])
            if resp.status_code == 200 and len(resp.content) > 5000:
                dest.write_bytes(resp.content)
                print(f"Saved {item['filename']} ({len(resp.content):,} bytes)")
            else:
                print(f"Failed {item['filename']}: HTTP {resp.status_code} ({len(resp.content)} bytes)")
        except Exception as e:
            print(f"Error downloading {item['filename']}: {e}")

if __name__ == "__main__":
    download_pdfs()
