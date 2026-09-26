import httpx
from pathlib import Path

SAMPLE_VIDEOS = [
    {
        "filename": "outdoor_adventure_escapes.mp4",
        "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
        "description": "Outdoor nature landscapes, mountains, drone footage"
    },
    {
        "filename": "tech_presentation_blazes.mp4",
        "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "description": "Technology demo video with people, screen presentation"
    },
    {
        "filename": "short_animation_bunny.mp4",
        "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "description": "Animated film with forest, rabbit, animals and nature"
    }
]

def download_videos():
    out_dir = Path("data/media/videos")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    headers = {"User-Agent": "Mozilla/5.0"}
    client = httpx.Client(timeout=60.0, follow_redirects=True, headers=headers)

    for item in SAMPLE_VIDEOS:
        dest = out_dir / item["filename"]
        if dest.exists() and dest.stat().st_size > 100000:
            print(f"Already exists: {item['filename']} ({dest.stat().st_size:,} bytes)")
            continue

        print(f"Downloading {item['filename']} from {item['url']}...")
        try:
            with client.stream("GET", item["url"]) as resp:
                if resp.status_code == 200:
                    with open(dest, "wb") as f:
                        for chunk in resp.iter_bytes(chunk_size=1024*1024):
                            f.write(chunk)
                    print(f"Saved {item['filename']} ({dest.stat().st_size:,} bytes)")
                else:
                    print(f"Failed {item['filename']}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"Error {item['filename']}: {e}")

if __name__ == "__main__":
    download_videos()
