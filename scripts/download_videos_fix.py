"""Fix: Download large videos from Blender Foundation + Internet Archive (working sources)"""
import sys, time, httpx
from pathlib import Path

BASE       = Path(__file__).parent.parent
VIDEOS_DIR = BASE / "data" / "media" / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# Blender Foundation direct + Internet Archive — all public domain / CC BY
VIDEOS = [
    {
        "filename": "big_buck_bunny_720p.mp4",
        "urls": [
            "https://download.blender.org/peach/bigbuckbunny_movies/BigBuckBunny_320x180.mp4",
            "https://archive.org/download/BigBuckBunny_124/Content/big_buck_bunny_720p_surround.mp4",
        ],
        "desc": "Big Buck Bunny - Blender animated film (forest, animals, nature)",
    },
    {
        "filename": "elephants_dream_720p.mp4",
        "urls": [
            "https://download.blender.org/ED/ed_1024_512kb.mp4",
            "https://archive.org/download/ElephantsDream/ed_1024_512kb.mp4",
        ],
        "desc": "Elephants Dream - Blender open movie (CC BY)",
    },
    {
        "filename": "sintel_trailer.mp4",
        "urls": [
            "https://download.blender.org/durian/trailer/sintel_trailer-480p.mp4",
            "https://archive.org/download/Sintel/sintel-2048-surround.mp4",
        ],
        "desc": "Sintel trailer - Blender animated short (fantasy, outdoor)",
    },
    {
        "filename": "cosmos_laundromat_preview.mp4",
        "urls": [
            "https://download.blender.org/films/cosmos-laundromat/cosmos_laundromat_720p.mp4",
            "https://archive.org/download/cosmos_laundromat/cosmos_laundromat_720p.mp4",
        ],
        "desc": "Cosmos Laundromat - Blender animated film (sheep, fantasy landscape)",
    },
    {
        "filename": "nature_wildlife_documentary.mp4",
        "urls": [
            "https://www.pexels.com/download/video/3571264/",
            "https://archive.org/download/WildlifeSafari/wildlife_safari_hd.mp4",
        ],
        "desc": "Wildlife nature documentary footage",
    },
    {
        "filename": "city_streets_timelapse.mp4",
        "urls": [
            "https://archive.org/download/CityTimelapse/city_timelapse_hd.mp4",
        ],
        "desc": "City streets timelapse urban footage",
    },
]

def human(n):
    for u in ("B","KB","MB","GB"):
        if n<1024: return f"{n:.1f} {u}"
        n/=1024
    return f"{n:.1f} TB"

def try_stream(client, url, dest):
    try:
        with client.stream("GET", url, timeout=180.0) as r:
            if r.status_code != 200:
                return False, f"HTTP {r.status_code}"
            cl = int(r.headers.get("content-length",0))
            done = 0
            with open(dest,"wb") as f:
                for chunk in r.iter_bytes(524288):
                    f.write(chunk); done+=len(chunk)
                    if cl:
                        pct=done/cl*100
                        sys.stdout.write(f"\r  [{('#'*int(pct/5)):<20}] {pct:.0f}% {human(done)}  ")
                        sys.stdout.flush()
            print(f"\r  OK  {dest.name}  {human(dest.stat().st_size):<14}")
            return True, None
    except Exception as e:
        if dest.exists(): dest.unlink(missing_ok=True)
        return False, str(e)

headers = {"User-Agent": "Mozilla/5.0 (compatible; AssetLens/1.0)"}
client = httpx.Client(follow_redirects=True, headers=headers)
ok=skip=fail=0

print("\n===== DOWNLOADING LARGE VIDEOS =====")
for item in VIDEOS:
    dest = VIDEOS_DIR / item["filename"]
    if dest.exists() and dest.stat().st_size > 500_000:
        print(f"  -- {item['filename']} ({human(dest.stat().st_size)})"); skip+=1; continue
    print(f"\n  >> {item['filename']}\n     {item['desc']}")
    success = False
    for url in item["urls"]:
        print(f"     Trying: {url[:70]}...")
        success, err = try_stream(client, url, dest)
        if success: break
        print(f"     x {err}")
    if success: ok+=1
    else: print(f"  !! All URLs failed for {item['filename']}"); fail+=1
    time.sleep(0.5)

total = sum(f.stat().st_size for f in VIDEOS_DIR.glob("*.mp4") if f.is_file())
vids  = sum(1 for _ in VIDEOS_DIR.glob("*.mp4"))
client.close()
print(f"\n  Downloaded: {ok}  Skipped: {skip}  Failed: {fail}")
print(f"  Videos folder: {vids} files, {human(total)}")
