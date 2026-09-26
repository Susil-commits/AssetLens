import os
from pathlib import Path
import httpx

# Public domain and CC-licensed image URLs from Wikimedia Commons and Unsplash (free to use)
SAMPLE_IMAGES = [
    {
        "filename": "living_room_interior.jpg",
        "url": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800&auto=format&fit=crop&q=80",
        "description": "Modern living room with yellow chair, sofa and wall art"
    },
    {
        "filename": "construction_site_crane.jpg",
        "url": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=800&auto=format&fit=crop&q=80",
        "description": "Construction worker on site with safety helmet and scaffolding"
    },
    {
        "filename": "woman_holding_cat.jpg",
        "url": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800&auto=format&fit=crop&q=80",
        "description": "Close up of an orange tabby cat looking at camera"
    },
    {
        "filename": "business_meeting.jpg",
        "url": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=800&auto=format&fit=crop&q=80",
        "description": "Group of business colleagues having a discussion in modern office"
    },
    {
        "filename": "sports_car_red.jpg",
        "url": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800&auto=format&fit=crop&q=80",
        "description": "Sports car driving on road"
    },
    {
        "filename": "mountain_lake_landscape.jpg",
        "url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&auto=format&fit=crop&q=80",
        "description": "Majestic mountain peaks with lake and forest"
    },
    {
        "filename": "delicious_pasta_dish.jpg",
        "url": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=800&auto=format&fit=crop&q=80",
        "description": "Plate of gourmet pasta with sauce and garnish"
    },
    {
        "filename": "dog_playing_park.jpg",
        "url": "https://images.unsplash.com/photo-1552053831-71594a27632d?w=800&auto=format&fit=crop&q=80",
        "description": "Golden retriever dog in green grassy field"
    },
    {
        "filename": "hospital_doctor_stethoscope.jpg",
        "url": "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?w=800&auto=format&fit=crop&q=80",
        "description": "Doctor wearing stethoscope and medical scrubs in clinic"
    },
    {
        "filename": "city_skyline_sunset.jpg",
        "url": "https://images.unsplash.com/photo-1477959858617-67f30bc75b82?auto=format&fit=crop&w=800&q=80",
        "description": "Skyscrapers of city skyline illuminated at golden hour sunset"
    },
    {
        "filename": "coffee_latte_art.jpg",
        "url": "https://images.unsplash.com/photo-1511920170033-f8396924c348?w=800&auto=format&fit=crop&q=80",
        "description": "Cup of hot cappuccino with leaf latte art on wooden table"
    },
    {
        "filename": "airplane_flying_clouds.jpg",
        "url": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=800&auto=format&fit=crop&q=80",
        "description": "Commercial passenger jet airliner flying above clouds"
    },
    {
        "filename": "modern_kitchen.jpg",
        "url": "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=800&auto=format&fit=crop&q=80",
        "description": "Clean luxury kitchen interior with marble island"
    },
    {
        "filename": "acoustic_guitar_player.jpg",
        "url": "https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=800&auto=format&fit=crop&q=80",
        "description": "Musician playing acoustic guitar with fingers on fretboard"
    },
    {
        "filename": "snowy_winter_forest.jpg",
        "url": "https://images.unsplash.com/photo-1483921020237-2ff51e8e4b22?w=800&auto=format&fit=crop&q=80",
        "description": "Winter evergreen forest covered in fresh white snow"
    },
    {
        "filename": "tropical_beach_ocean.jpg",
        "url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&auto=format&fit=crop&q=80",
        "description": "Tropical paradise beach with turquoise sea water and white sand"
    },
    {
        "filename": "vintage_camera_photo.jpg",
        "url": "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&auto=format&fit=crop&q=80",
        "description": "Classic vintage retro film camera on desk"
    }
]

def download_images():
    target_dir = Path("data/media/images")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    client = httpx.Client(timeout=30.0, follow_redirects=True, headers=headers)
    
    downloaded = 0
    for item in SAMPLE_IMAGES:
        dest = target_dir / item["filename"]
        if dest.exists() and dest.stat().st_size > 1000:
            print(f"Already exists: {item['filename']}")
            downloaded += 1
            continue
        
        print(f"Downloading {item['filename']}...")
        try:
            resp = client.get(item["url"])
            if resp.status_code == 200 and len(resp.content) > 1000:
                dest.write_bytes(resp.content)
                print(f"Saved: {item['filename']} ({len(resp.content):,} bytes)")
                downloaded += 1
            else:
                print(f"Failed to download {item['filename']}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"Error downloading {item['filename']}: {e}")

    print(f"Successfully prepared {downloaded}/{len(SAMPLE_IMAGES)} real test images in {target_dir}")

if __name__ == "__main__":
    download_images()
