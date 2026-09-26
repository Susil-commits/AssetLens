import httpx
from pathlib import Path

SAMPLE_PDFS = [
    {
        "filename": "tracemonkey_compiler_paper.pdf",
        "url": "https://raw.githubusercontent.com/mozilla/pdf.js/master/test/pdfs/tracemonkey.pdf",
        "description": "TraceMonkey JavaScript Compiler paper"
    },
    {
        "filename": "residential_architecture_brochure.pdf",
        "url": "https://raw.githubusercontent.com/foliojs/pdfkit/master/docs/guide.pdf",
        "description": "PDFKit Architecture Guide and documentation with graphics"
    }
]

def download_more():
    out_dir = Path("data/media/documents")
    out_dir.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0"}
    client = httpx.Client(timeout=30.0, follow_redirects=True, headers=headers)

    for item in SAMPLE_PDFS:
        dest = out_dir / item["filename"]
        if dest.exists() and dest.stat().st_size > 5000:
            print(f"Already exists: {item['filename']}")
            continue
        try:
            resp = client.get(item["url"])
            if resp.status_code == 200 and len(resp.content) > 1000:
                dest.write_bytes(resp.content)
                print(f"Saved {item['filename']} ({len(resp.content):,} bytes)")
            else:
                print(f"Failed {item['filename']}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"Error {item['filename']}: {e}")

if __name__ == "__main__":
    download_more()
