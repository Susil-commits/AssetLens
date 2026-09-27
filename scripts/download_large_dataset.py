"""
AssetLens — Large Dataset Downloader
=====================================
Downloads a substantial mixed-media dataset from free, public-domain sources.
Target: ~1-2 GB of real images, videos, and PDFs.

Run from the AssetLens project root:
    python scripts/download_large_dataset.py

Sources:
- Videos  : Blender Foundation open movies (CC BY), Google Test Videos (public)
- Images  : Unsplash (free license, w=1920 for large files)
- PDFs    : arXiv papers (open access), US Gov / NASA public reports
"""

import sys
import time
import httpx
from pathlib import Path

BASE       = Path(__file__).parent.parent
IMAGES_DIR = BASE / "data" / "media" / "images"
VIDEOS_DIR = BASE / "data" / "media" / "videos"
DOCS_DIR   = BASE / "data" / "media" / "documents"
for d in (IMAGES_DIR, VIDEOS_DIR, DOCS_DIR):
    d.mkdir(parents=True, exist_ok=True)

LARGE_VIDEOS = [
    {"filename": "big_buck_bunny_1080p.mp4",       "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",              "desc": "Big Buck Bunny animated film forest/animals (276 MB)"},
    {"filename": "elephants_dream_720p.mp4",        "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",            "desc": "Elephants Dream Blender animated short (200 MB)"},
    {"filename": "tears_of_steel_vfx.mp4",          "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",              "desc": "Tears of Steel sci-fi VFX short film (338 MB)"},
    {"filename": "for_bigger_escapes_outdoor.mp4",  "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",         "desc": "Outdoor adventure landscape (50 MB)"},
    {"filename": "for_bigger_blazes_tech.mp4",      "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",          "desc": "Technology demo presentation (50 MB)"},
    {"filename": "subaru_outback_car_driving.mp4",  "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/SubaruOutbackOnStreetAndDirt.mp4", "desc": "Subaru car on road and dirt (66 MB)"},
    {"filename": "volkswagen_gti_review.mp4",        "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/VolkswagenGTIReview.mp4",      "desc": "Volkswagen GTI car review (50 MB)"},
    {"filename": "we_are_going_on_bullrun.mp4",     "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4",       "desc": "Road trip Bullrun adventure footage (66 MB)"},
]

LARGE_IMAGES = [
    {"filename": "architecture_modern_house.jpg",        "url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "architecture_apartment_exterior.jpg",  "url": "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "interior_luxury_bedroom_002.jpg",      "url": "https://images.unsplash.com/photo-1540518614846-7eded433c457?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "interior_open_plan_living.jpg",        "url": "https://images.unsplash.com/photo-1600210492493-0946911123ea?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "interior_bathroom_marble.jpg",         "url": "https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "interior_home_office.jpg",             "url": "https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "interior_dining_room.jpg",             "url": "https://images.unsplash.com/photo-1615529328331-f8917597711f?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "real_estate_house_for_sale.jpg",       "url": "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "real_estate_aerial_neighbourhood.jpg", "url": "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "real_estate_rooftop_terrace.jpg",      "url": "https://images.unsplash.com/photo-1572120360610-d971b9d7767c?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "real_estate_garden_pathway.jpg",       "url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "construction_blueprint_plan.jpg",      "url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "construction_concrete_pour.jpg",       "url": "https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "construction_scaffolding_city.jpg",    "url": "https://images.unsplash.com/photo-1590274853856-f22d5ee3d228?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "nature_aerial_forest.jpg",             "url": "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "nature_waterfall_jungle.jpg",          "url": "https://images.unsplash.com/photo-1465146344425-f00d5f5c8f07?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "nature_desert_sand_dunes.jpg",         "url": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "nature_aurora_borealis.jpg",           "url": "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "nature_sunset_ocean.jpg",              "url": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "nature_lavender_fields.jpg",           "url": "https://images.unsplash.com/photo-1468581264429-2548ef9eb732?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "people_woman_yoga.jpg",                "url": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "people_family_picnic.jpg",             "url": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "people_chef_cooking.jpg",              "url": "https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "people_scientist_lab.jpg",             "url": "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "people_surfer_wave.jpg",               "url": "https://images.unsplash.com/photo-1502680390469-be75c86b636f?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "people_student_library.jpg",           "url": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "tech_server_data_center.jpg",          "url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "tech_drone_aerial.jpg",                "url": "https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "tech_laptop_code.jpg",                 "url": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "food_sushi_platter.jpg",               "url": "https://images.unsplash.com/photo-1553621042-f6e147245754?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "food_burger_closeup.jpg",              "url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "food_wine_pouring.jpg",                "url": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "animal_lion_savanna.jpg",              "url": "https://images.unsplash.com/photo-1547721664-56be5d5b24d1?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "animal_elephant_herd.jpg",             "url": "https://images.unsplash.com/photo-1564760055775-d63b17a55c44?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "animal_horse_galloping.jpg",           "url": "https://images.unsplash.com/photo-1534773728080-33d31da27ae5?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "urban_tokyo_street_night.jpg",         "url": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "urban_new_york_times_square.jpg",      "url": "https://images.unsplash.com/photo-1485871981521-5b1fd3805eee?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "urban_paris_eiffel_tower.jpg",         "url": "https://images.unsplash.com/photo-1499856871958-5b9357976b82?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "sports_basketball_court.jpg",          "url": "https://images.unsplash.com/photo-1546519638397-a91d348f9a33?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "sports_swimming_pool_race.jpg",        "url": "https://images.unsplash.com/photo-1530549387789-4c1017266635?w=1920&auto=format&fit=crop&q=85"},
    {"filename": "sports_gym_weights.jpg",               "url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=1920&auto=format&fit=crop&q=85"},
]

LARGE_PDFS = [
    {"filename": "attention_is_all_you_need.pdf",    "url": "https://arxiv.org/pdf/1706.03762.pdf"},
    {"filename": "deep_residual_learning_resnet.pdf","url": "https://arxiv.org/pdf/1512.03385.pdf"},
    {"filename": "bert_pretraining_nlp.pdf",         "url": "https://arxiv.org/pdf/1810.04805.pdf"},
    {"filename": "generative_adversarial_nets.pdf",  "url": "https://arxiv.org/pdf/1406.2661.pdf"},
    {"filename": "clip_visual_models.pdf",           "url": "https://arxiv.org/pdf/2103.00020.pdf"},
    {"filename": "nrel_renewable_energy_report.pdf", "url": "https://www.nrel.gov/docs/fy21osti/77650.pdf"},
    {"filename": "us_housing_guidelines.pdf",        "url": "https://www.hud.gov/sites/dfiles/OCHCO/documents/49001c13HSGH.pdf"},
]


def human_size(n):
    for u in ("B","KB","MB","GB"):
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def stream_dl(client, url, dest, label):
    try:
        with client.stream("GET", url, timeout=300.0) as r:
            if r.status_code != 200:
                print(f"  x HTTP {r.status_code}"); return False
            total = int(r.headers.get("content-length", 0))
            done = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_bytes(65536):
                    f.write(chunk); done += len(chunk)
                    if total:
                        pct = done/total*100
                        sys.stdout.write(f"\r  [{('#'*int(pct/5)):<20}] {pct:.0f}% {human_size(done)}  ")
                        sys.stdout.flush()
            print(f"\r  OK  {label}  {human_size(dest.stat().st_size):<14}")
            return True
    except Exception as e:
        print(f"  x  {e}"); dest.unlink(missing_ok=True); return False


def simple_dl(client, url, dest, label):
    try:
        r = client.get(url, timeout=60.0)
        if r.status_code == 200 and len(r.content) > 1000:
            dest.write_bytes(r.content)
            print(f"  OK  {label}  {human_size(len(r.content))}"); return True
        print(f"  x  HTTP {r.status_code}"); return False
    except Exception as e:
        print(f"  x  {e}"); return False


def run():
    headers = {"User-Agent": "Mozilla/5.0 AssetLens/1.0"}
    client = httpx.Client(follow_redirects=True, headers=headers)
    ok = skip = fail = 0

    print("\n===== VIDEOS =====")
    for item in LARGE_VIDEOS:
        dest = VIDEOS_DIR / item["filename"]
        if dest.exists() and dest.stat().st_size > 100_000:
            print(f"  -- {item['filename']} ({human_size(dest.stat().st_size)})"); skip += 1; continue
        print(f"\n  >> {item['filename']}\n     {item['desc']}")
        if stream_dl(client, item["url"], dest, item["filename"]): ok += 1
        else: fail += 1
        time.sleep(0.2)

    print("\n===== IMAGES =====")
    for item in LARGE_IMAGES:
        dest = IMAGES_DIR / item["filename"]
        if dest.exists() and dest.stat().st_size > 5_000:
            print(f"  -- {item['filename']}"); skip += 1; continue
        if simple_dl(client, item["url"], dest, item["filename"]): ok += 1
        else: fail += 1
        time.sleep(0.1)

    print("\n===== PDFs =====")
    for item in LARGE_PDFS:
        dest = DOCS_DIR / item["filename"]
        if dest.exists() and dest.stat().st_size > 5_000:
            print(f"  -- {item['filename']}"); skip += 1; continue
        if simple_dl(client, item["url"], dest, item["filename"]): ok += 1
        else: fail += 1
        time.sleep(0.5)

    total_bytes = sum(f.stat().st_size for d in (IMAGES_DIR, VIDEOS_DIR, DOCS_DIR) for f in d.glob("*") if f.is_file())
    imgs = sum(1 for _ in IMAGES_DIR.glob("*.jpg")) + sum(1 for _ in IMAGES_DIR.glob("*.png"))
    vids = sum(1 for _ in VIDEOS_DIR.glob("*.mp4"))
    pdfs = sum(1 for _ in DOCS_DIR.glob("*.pdf"))
    print(f"\n===== DONE =====")
    print(f"  Downloaded: {ok}  Skipped: {skip}  Failed: {fail}")
    print(f"  Assets    : {imgs} images + {vids} videos + {pdfs} PDFs")
    print(f"  Total size: {human_size(total_bytes)}")
    client.close()

if __name__ == "__main__":
    run()
