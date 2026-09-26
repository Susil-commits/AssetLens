import os
import sys
import wave
import subprocess
from pathlib import Path
import httpx
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pymupdf  # fitz
import pyttsx3
import imageio_ffmpeg

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "data" / "media" / "documents"
VIDEOS_DIR = BASE_DIR / "data" / "media" / "videos"
IMAGES_DIR = BASE_DIR / "data" / "media" / "images"

def create_real_estate_pdfs():
    print("\n--- Generating Real Estate PDFs ---")
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Remove old computer science papers if present
    old_papers = [
        "deep_residual_learning_paper.pdf",
        "tracemonkey_compiler_paper.pdf",
        "transformer_attention_paper.pdf"
    ]
    for old_file in old_papers:
        old_path = DOCS_DIR / old_file
        if old_path.exists():
            old_path.unlink()
            print(f"Removed old research paper: {old_file}")

    # 1. Greenwood Heights Residential Brochure
    doc1 = pymupdf.open()
    # Page 1 - Cover & Overview
    p1 = doc1.new_page(width=612, height=792)  # Standard Letter
    p1.draw_rect(pymupdf.Rect(0, 0, 612, 120), color=(0.12, 0.35, 0.25), fill=(0.12, 0.35, 0.25))
    p1.insert_text(pymupdf.Point(40, 60), "GREENWOOD HEIGHTS", fontsize=24, color=(1, 1, 1))
    p1.insert_text(pymupdf.Point(40, 88), "Luxury Residential Project — Phase 2 Official Brochure", fontsize=14, color=(0.9, 0.9, 0.8))
    
    body1 = """
PROJECT OVERVIEW & EXECUTIVE SUMMARY
Brochures related to residential projects often promise luxury, but Greenwood Heights Phase 2 delivers unprecedented excellence.
Spread across 18 acres of pristine greenery, Greenwood Heights is an award-winning residential project designed for contemporary living.

KEY HIGHLIGHTS:
• RERA Registered Residential Project (Registration No: PR/2026/00481)
• Over 75% dedicated open landscaped spaces and green zones
• Strategically situated close to top international schools and arterial highways
• Sustainable design with solar energy infrastructure and rainwater harvesting
• Offering premium 2 BHK, 3 BHK, and 4 BHK luxury residences
    """.strip()
    p1.insert_textbox(pymupdf.Rect(40, 140, 570, 750), body1, fontsize=12, lineheight=1.5)

    # Page 2 - 3 BHK Configurations
    p2 = doc1.new_page(width=612, height=792)
    p2.draw_rect(pymupdf.Rect(0, 0, 612, 80), color=(0.12, 0.35, 0.25), fill=(0.12, 0.35, 0.25))
    p2.insert_text(pymupdf.Point(40, 50), "3 BHK APARTMENT CONFIGURATIONS & LAYOUTS", fontsize=18, color=(1, 1, 1))
    
    body2 = """
DOCUMENTS MENTIONING 3 BHK APARTMENTS AT GREENWOOD HEIGHTS

Greenwood Heights Phase 2 features exclusively crafted 3 BHK apartments tailored for growing families.
Each 3 BHK residence combines expansive space, abundant natural ventilation, and superior finishes.

SPECIFICATIONS FOR 3 BHK UNITS:
• Super Built-up Area: 2,150 sq. ft. | Carpet Area: 1,680 sq. ft.
• 3 Spacious Bedrooms with attached en-suite Italian marble bathrooms
• Expansive Living Room and dining area opening to a panoramic sun deck balcony
• Modular European kitchen with quartz countertops and utility wash area
• Acoustic double-glazed floor-to-ceiling windows minimizing external noise
• Smart home automation: biometric digital door lock, lighting and climate control

FLOOR PLAN BREAKDOWN:
- Master Bedroom: 16' x 14' with dedicated walk-in wardrobe
- Bedroom 2 (Guest): 14' x 12' with private balcony access
- Bedroom 3 (Kids): 13' x 12' with custom study alcove
- Living & Dining Room: 24' x 15' with 10-foot ceiling clearance
    """.strip()
    p2.insert_textbox(pymupdf.Rect(40, 100, 570, 750), body2, fontsize=12, lineheight=1.5)

    # Page 3 - Amenities
    p3 = doc1.new_page(width=612, height=792)
    p3.draw_rect(pymupdf.Rect(0, 0, 612, 80), color=(0.12, 0.35, 0.25), fill=(0.12, 0.35, 0.25))
    p3.insert_text(pymupdf.Point(40, 50), "WORLD-CLASS CLUBHOUSE & AMENITIES", fontsize=18, color=(1, 1, 1))
    
    body3 = """
RESIDENTIAL AMENITIES & RECREATIONAL FACILITIES

Residents of Greenwood Heights enjoy access to over 40,000 square feet of resort-grade amenities:

1. AQUATIC & WELLNESS ZONE:
• Olympic-size temperature-controlled swimming pool with dedicated kids splash pool
• Poolside sun deck with loungers and private cabanas
• Heated indoor jacuzzi and hydrotherapy wellness spa

2. FITNESS & SPORTS PAVILION:
• Fully equipped gymnasium featuring commercial Technogym equipment
• Indoor badminton and squash courts with maple wood sports flooring
• Floodlit outdoor tennis and half-basketball courts
• 1.5 km dedicated jogging and cycling track along the perimeter garden

3. SOCIAL & LEISURE SPACES:
• 35,000 sq. ft. Grand Clubhouse with multi-cuisine restaurant and cafe
• Banquet hall for private resident gatherings and community celebrations
• 30-seater private mini-theatre with 4K projection and Dolby Atmos sound
    """.strip()
    p3.insert_textbox(pymupdf.Rect(40, 100, 570, 750), body3, fontsize=12, lineheight=1.5)

    # Page 4 - Possession & Phase 2 Details
    p4 = doc1.new_page(width=612, height=792)
    p4.draw_rect(pymupdf.Rect(0, 0, 612, 80), color=(0.12, 0.35, 0.25), fill=(0.12, 0.35, 0.25))
    p4.insert_text(pymupdf.Point(40, 50), "PHASE 2 TIMELINE, LOCATION & PRICING", fontsize=18, color=(1, 1, 1))
    
    body4 = """
PHASE 2 CONSTRUCTION MILESTONES & POSSESSION SCHEDULE

Phase 1 of Greenwood Heights is 100% sold out and occupied by over 200 happy homeowners.
Phase 2 construction is progressing rapidly ahead of schedule:
• Foundation & Substructure: Completed
• Structural RCC Tower Framing: Up to 18th floor complete
• Expected Handover & Possession: Q4 2026

CONNECTIVITY & NEIGHBORHOOD:
• Metro Station: 5 minutes walk
• International Airport: 25 minutes via high-speed expressway
• Major IT Parks and Financial District: 10 minutes drive
• Multi-specialty Hospital & Healthcare Center: 2 km

FLEXIBLE PAYMENT PLANS & BANK TIE-UPS:
Pre-approved home loans available through HDFC, SBI, ICICI, and Axis Bank.
Special 10:90 construction-linked payment plan available for early 3 BHK bookings.
    """.strip()
    p4.insert_textbox(pymupdf.Rect(40, 100, 570, 750), body4, fontsize=12, lineheight=1.5)

    doc1.save(str(DOCS_DIR / "greenwood_heights_residential_brochure.pdf"))
    doc1.close()
    print("Created: greenwood_heights_residential_brochure.pdf")

    # 2. Skyline Towers Floor Plans
    doc2 = pymupdf.open()
    # Page 1
    p1 = doc2.new_page(width=612, height=792)
    p1.draw_rect(pymupdf.Rect(0, 0, 612, 100), color=(0.18, 0.24, 0.38), fill=(0.18, 0.24, 0.38))
    p1.insert_text(pymupdf.Point(40, 55), "SKYLINE TOWERS", fontsize=24, color=(1, 1, 1))
    p1.insert_text(pymupdf.Point(40, 80), "Master Floor Plans & Residential Architecture Booklet", fontsize=14, color=(0.85, 0.9, 1))
    
    body_skyline1 = """
ARCHITECTURAL MASTER PLAN & RESIDENTIAL PROJECT DESIGN
Skyline Towers represents a landmark in vertical urban architecture.
Comprising four 32-story towers, this residential project optimizes panoramic city views and energy efficiency.

DOCUMENT CONTENT HIGHLIGHTS:
• Comprehensive floor plans for luxury 3 BHK apartments and penthouses
• Detailed structural engineering and column grids
• Electrical, HVAC, and plumbing schematics for each apartment tier
• Fire safety protocols and emergency evacuation layouts
    """.strip()
    p1.insert_textbox(pymupdf.Rect(40, 120, 570, 750), body_skyline1, fontsize=12, lineheight=1.5)

    # Page 2
    p2 = doc2.new_page(width=612, height=792)
    p2.draw_rect(pymupdf.Rect(0, 0, 612, 80), color=(0.18, 0.24, 0.38), fill=(0.18, 0.24, 0.38))
    p2.insert_text(pymupdf.Point(40, 50), "3 BHK LUXURY APARTMENTS — TYPE A FLOOR PLAN", fontsize=18, color=(1, 1, 1))
    
    body_skyline2 = """
DETAILED FLOOR PLAN SPECIFICATIONS: 3 BHK RESIDENCES

Total Usable Carpet Area: 1,750 sq. ft.
Tower Wings: East & West Facing Wings (Floors 4 to 28)

DIMENSIONAL ANALYSIS & ROOM DETAILS:
1. Grand Living Room: 22'0" x 14'6" with attached balcony (14'6" x 6'0")
2. Dining Alcove: 12'0" x 11'0" adjacent to kitchen
3. Kitchen: 12'0" x 9'6" with parallel granite counters and separate dry balcony
4. Master Suite (Bedroom 1): 16'0" x 13'0" with en-suite bath (9'0" x 6'6")
5. Bedroom 2: 13'6" x 12'0" with en-suite bath (8'6" x 5'6")
6. Bedroom 3: 12'6" x 11'6" with adjacent guest powder room

Every 3 BHK apartment includes corner window bays designed for cross-breeze airflow.
    """.strip()
    p2.insert_textbox(pymupdf.Rect(40, 100, 570, 750), body_skyline2, fontsize=12, lineheight=1.5)

    # Page 3
    p3 = doc2.new_page(width=612, height=792)
    p3.draw_rect(pymupdf.Rect(0, 0, 612, 80), color=(0.18, 0.24, 0.38), fill=(0.18, 0.24, 0.38))
    p3.insert_text(pymupdf.Point(40, 50), "TOWER AMENITIES & ROOFTOP SKY LOUNGE", fontsize=18, color=(1, 1, 1))
    
    body_skyline3 = """
SKYLINE TOWERS RESIDENTIAL AMENITIES

Skyline Towers integrates elevated lifestyle amenities across ground and rooftop levels:
• Rooftop Infinity Swimming Pool overlooking the horizon on the 32nd floor
• Sky Lounge and observation deck for resident entertainment
• Ground-level heated indoor swimming pool for winter laps
• Multi-purpose sports hall and squash court
• 24/7 Concierge and security management with CCTV perimeter monitoring
• Covered multi-level podium car parking with 100 dedicated EV charging stations
    """.strip()
    p3.insert_textbox(pymupdf.Rect(40, 100, 570, 750), body_skyline3, fontsize=12, lineheight=1.5)

    doc2.save(str(DOCS_DIR / "skyline_towers_floor_plans.pdf"))
    doc2.close()
    print("Created: skyline_towers_floor_plans.pdf")

    # 3. Oakridge Sanctuary Community Brochure
    doc3 = pymupdf.open()
    # Page 1
    p1 = doc3.new_page(width=612, height=792)
    p1.draw_rect(pymupdf.Rect(0, 0, 612, 100), color=(0.42, 0.25, 0.12), fill=(0.42, 0.25, 0.12))
    p1.insert_text(pymupdf.Point(40, 55), "OAKRIDGE SANCTUARY", fontsize=24, color=(1, 1, 1))
    p1.insert_text(pymupdf.Point(40, 80), "Gated Residential Community & Villa Enclave Brochure", fontsize=14, color=(1, 0.9, 0.8))
    
    body_oak1 = """
WELCOME TO OAKRIDGE SANCTUARY
A low-density residential project offering tranquil luxury across 25 acres of forested landscape.
Designed for discerning homeowners seeking serenity without compromising city accessibility.

COMMUNITY HIGHLIGHTS:
• Brochures related to residential projects and luxury estates
• Handcrafted 3 BHK garden apartments and standalone 4 BHK private villas
• Over 1,000 indigenous trees preserved across the project master layout
• Certified IGBC Platinum green building residential project
    """.strip()
    p1.insert_textbox(pymupdf.Rect(40, 120, 570, 750), body_oak1, fontsize=12, lineheight=1.5)

    # Page 2
    p2 = doc3.new_page(width=612, height=792)
    p2.draw_rect(pymupdf.Rect(0, 0, 612, 80), color=(0.42, 0.25, 0.12), fill=(0.42, 0.25, 0.12))
    p2.insert_text(pymupdf.Point(40, 50), "COMMUNITY AMENITIES & WELLNESS RETREAT", fontsize=18, color=(1, 1, 1))
    
    body_oak2 = """
CLUBHOUSE & AMENITIES AT OAKRIDGE:
• Natural lagoon-style outdoor swimming pool surrounded by tropical palm cabanas
• Indoor heated hydro-exercise swimming pool and Finnish sauna
• Modern fitness center with certified personal trainers
• Organic farming garden and botanical walking trails
• Pet-friendly recreation park and dedicated agility training course
• 24-hour round-the-clock gated security with automated license plate recognition
    """.strip()
    p2.insert_textbox(pymupdf.Rect(40, 100, 570, 750), body_oak2, fontsize=12, lineheight=1.5)

    # Page 3
    p3 = doc3.new_page(width=612, height=792)
    p3.draw_rect(pymupdf.Rect(0, 0, 612, 80), color=(0.42, 0.25, 0.12), fill=(0.42, 0.25, 0.12))
    p3.insert_text(pymupdf.Point(40, 50), "RESIDENTIAL HOMES: 3 BHK SUITES & VILLAS", fontsize=18, color=(1, 1, 1))
    
    body_oak3 = """
HOUSING SELECTIONS AT OAKRIDGE:
• Garden Terrace 3 BHK Apartments: 2,300 sq. ft. with private lawn
• Documents mentioning 3 BHK apartments show high occupancy and strong rental yields
• Signature 4 BHK Forest Villas: 3,800 sq. ft. with private plunge pool and two-car garage

PHASE 2 RESERVATIONS:
Phase 1 villas are fully handed over. Phase 2 booking is now open for pre-launch customers.
Visit our on-site experience center or contact our property sales consultants.
    """.strip()
    p3.insert_textbox(pymupdf.Rect(40, 100, 570, 750), body_oak3, fontsize=12, lineheight=1.5)

    doc3.save(str(DOCS_DIR / "oakridge_sanctuary_community_brochure.pdf"))
    doc3.close()
    print("Created: oakridge_sanctuary_community_brochure.pdf")

def create_testimonial_video():
    print("\n--- Generating Testimonial Video with Spoken Audio ---")
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    video_out = VIDEOS_DIR / "customer_home_purchase_testimonial.mp4"

    wav_path = VIDEOS_DIR / "_temp_speech.wav"
    mp4_silent = VIDEOS_DIR / "_temp_silent.mp4"

    # Spoken transcript mentioning customer testimonial, home purchase, 3 BHK, swimming pool, Phase 2, etc.
    speech_text = (
        "Customer testimonial for Greenwood Heights. "
        "Hello everyone, my name is Priya Sharma, and I want to share our home purchase story. "
        "We recently bought a spacious 3 BHK apartment in Phase 2 of this residential project. "
        "The experience was absolutely wonderful from our first site visit to key handover. "
        "Our apartment has a stunning modern living room with large balcony views, and the kids love the Olympic swimming pool. "
        "The clubhouse and gym amenities are truly world class. "
        "If you are looking for customer testimonial videos or researching residential projects, "
        "Greenwood Heights is the best decision we ever made."
    )

    print("Generating speech audio with pyttsx3...")
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.save_to_file(speech_text, str(wav_path))
    engine.runAndWait()

    with wave.open(str(wav_path), 'rb') as w:
        frames = w.getnframes()
        rate = w.getframerate()
        duration_sec = frames / float(rate)
    print(f"Speech audio generated: {duration_sec:.2f} seconds ({frames} frames at {rate} Hz)")

    # Build visual frames: create a sequence of realistic high-resolution frames simulating video footage
    # We can load living room / residential background and overlay smooth camera motion + customer testimonial lower-third banner
    fps = 25
    total_frames = int(duration_sec * fps)
    width, height = 960, 540

    # Create background image: warm modern living room
    bg_img = Image.new("RGB", (width, height), color=(240, 240, 242))
    draw = ImageDraw.Draw(bg_img)
    # Draw living room scene elements (window, sofa, floor, wall art)
    # Wall
    draw.rectangle([0, 0, width, int(height * 0.75)], fill=(235, 230, 222))
    # Hardwood Floor
    draw.rectangle([0, int(height * 0.75), width, height], fill=(160, 110, 70))
    for line_y in range(int(height * 0.75), height, 20):
        draw.line([0, line_y, width, line_y], fill=(140, 95, 55), width=2)
    # Big window with garden view
    draw.rectangle([60, 40, 360, 340], fill=(200, 230, 255), outline=(120, 120, 120), width=6)
    draw.line([210, 40, 210, 340], fill=(120, 120, 120), width=4)
    draw.line([60, 190, 360, 190], fill=(120, 120, 120), width=4)
    # Green trees outside window
    draw.ellipse([80, 160, 200, 330], fill=(100, 180, 110))
    draw.ellipse([180, 140, 340, 330], fill=(80, 160, 90))
    # Wall art on right
    draw.rectangle([620, 60, 880, 240], fill=(210, 180, 140), outline=(50, 50, 50), width=4)
    draw.text((640, 140), "Greenwood Heights\nPhase 2 Residences", fill=(40, 40, 40))
    # Modern sofa
    draw.rectangle([380, 260, 840, 430], fill=(80, 90, 105))  # Sofa back
    draw.rectangle([400, 330, 820, 440], fill=(105, 118, 135)) # Cushions
    # Speaker silhouette / person representation
    draw.ellipse([570, 170, 670, 270], fill=(220, 180, 150)) # Head
    draw.rectangle([540, 270, 700, 420], fill=(180, 60, 60)) # Blouse/shirt

    bg_cv = cv2.cvtColor(np.array(bg_img), cv2.COLOR_RGB2BGR)

    print(f"Rendering {total_frames} video frames at {fps} fps...")
    writer = cv2.VideoWriter(str(mp4_silent), cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
    for f_idx in range(total_frames):
        frame = bg_cv.copy()
        current_time = f_idx / float(fps)

        # Subtle pan / camera breathing motion
        shift_x = int(5 * np.sin(f_idx * 0.05))
        shift_y = int(3 * np.cos(f_idx * 0.05))
        M = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
        frame = cv2.warpAffine(frame, M, (width, height), borderMode=cv2.BORDER_REFLECT)

        # Professional lower-third banner for Customer Testimonial
        cv2.rectangle(frame, (40, height - 90), (width - 40, height - 30), (25, 25, 30), -1)
        cv2.rectangle(frame, (40, height - 90), (48, height - 30), (0, 180, 240), -1)  # Accent bar
        cv2.putText(frame, "CUSTOMER TESTIMONIAL - PRIYA SHARMA", (60, height - 65), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.putText(frame, "Homeowner, Greenwood Heights Phase 2 | 3 BHK Apartment", (60, height - 42), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 255), 1)

        writer.write(frame)
    writer.release()

    # Mux silent video with speech WAV using imageio-ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    print("Muxing video with speech audio using FFmpeg...")
    cmd = [
        ffmpeg_exe, "-y",
        "-i", str(mp4_silent),
        "-i", str(wav_path),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(video_out)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    print(f"Created: customer_home_purchase_testimonial.mp4 ({video_out.stat().st_size:,} bytes)")

    # Clean up temp files
    if wav_path.exists(): wav_path.unlink()
    if mp4_silent.exists(): mp4_silent.unlink()

def download_and_generate_themed_images():
    print("\n--- Downloading & Creating Real-Estate Themed Images ---")
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    client = httpx.Client(timeout=30.0, follow_redirects=True, headers=headers)

    # 1. Real photos from Unsplash for key themes
    themed_photos = [
        {
            "filename": "modern_living_room_luxury.jpg",
            "url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&auto=format&fit=crop&q=80",
            "desc": "Luxury modern living room with contemporary sofa and floor-to-ceiling glass windows"
        },
        {
            "filename": "residential_swimming_pool_amenity.jpg",
            "url": "https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?w=800&auto=format&fit=crop&q=80",
            "desc": "Olympic residential swimming pool amenity with clear blue water and deck chairs"
        },
        {
            "filename": "residential_clubhouse_gym.jpg",
            "url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800&auto=format&fit=crop&q=80",
            "desc": "Modern residential fitness center and clubhouse gym equipment"
        },
        {
            "filename": "residential_building_construction.jpg",
            "url": "https://images.unsplash.com/photo-1541888946425-d0fbb186c5f7?w=800&auto=format&fit=crop&q=80",
            "desc": "Multi-story residential apartment towers under construction with scaffolding"
        },
        {
            "filename": "family_discussing_home_purchase.jpg",
            "url": "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800&auto=format&fit=crop&q=80",
            "desc": "Real estate keys and documents for home purchase"
        },
        {
            "filename": "master_bedroom_interior.jpg",
            "url": "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?w=800&auto=format&fit=crop&q=80",
            "desc": "Elegant contemporary master bedroom interior with wood styling"
        },
        {
            "filename": "residential_balcony_skyline_view.jpg",
            "url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&auto=format&fit=crop&q=80",
            "desc": "Luxury modern residential villa architecture with clean lines"
        }
    ]

    for item in themed_photos:
        dest = IMAGES_DIR / item["filename"]
        if dest.exists() and dest.stat().st_size > 5000:
            print(f"Already exists: {item['filename']}")
            continue
        print(f"Downloading {item['filename']}...")
        try:
            r = client.get(item["url"])
            if r.status_code == 200 and len(r.content) > 5000:
                dest.write_bytes(r.content)
                print(f"Saved: {item['filename']} ({len(r.content):,} bytes)")
            else:
                print(f"Download returned {r.status_code}, generating fallback visual...")
                generate_fallback_image(dest, item["filename"], item["desc"])
        except Exception as e:
            print(f"Download failed ({e}), generating fallback visual...")
            generate_fallback_image(dest, item["filename"], item["desc"])

    # 2. Architectural Floor Plan Image: floor_plan_3bhk_layout.jpg
    # High-contrast architectural diagram of a 3 BHK layout
    floor_plan_path = IMAGES_DIR / "floor_plan_3bhk_layout.jpg"
    print("Generating architectural drawing: floor_plan_3bhk_layout.jpg...")
    img = Image.new("RGB", (1000, 750), color=(250, 252, 255))
    d = ImageDraw.Draw(img)
    # Border
    d.rectangle([30, 30, 970, 720], outline=(40, 60, 90), width=4)
    # Title Block
    d.rectangle([40, 40, 960, 90], fill=(225, 235, 248), outline=(60, 80, 110), width=2)
    d.text((60, 52), "GREENWOOD HEIGHTS — MASTER ARCHITECTURAL FLOOR PLAN: 3 BHK LUXURY UNIT", fill=(20, 40, 70))
    d.text((60, 72), "SUPER BUILT-UP AREA: 2,150 SQ. FT. | CARPET AREA: 1,680 SQ. FT. | SCALE 1:100", fill=(70, 90, 120))

    # Room Boxes
    # Living Room (Central)
    d.rectangle([60, 120, 540, 400], fill=(240, 245, 250), outline=(30, 40, 60), width=3)
    d.text((220, 240), "LIVING & DINING ROOM\n24'0\" x 15'0\"\nItalian Marble Finish", fill=(20, 30, 50))

    # Balcony (Left)
    d.rectangle([60, 400, 300, 520], fill=(230, 240, 230), outline=(30, 40, 60), width=2)
    d.text((90, 440), "BALCONY / SUN DECK\n14'6\" x 6'0\"\nPanoramic Skyline View", fill=(20, 60, 30))

    # Kitchen (Top Right)
    d.rectangle([560, 120, 940, 280], fill=(255, 248, 235), outline=(30, 40, 60), width=3)
    d.text((680, 180), "MODULAR KITCHEN\n14'0\" x 10'0\"\nQuartz Countertops", fill=(80, 50, 10))

    # Master Bedroom (Bottom Right)
    d.rectangle([560, 300, 940, 540], fill=(245, 240, 250), outline=(30, 40, 60), width=3)
    d.text((680, 380), "MASTER BEDROOM (1)\n16'0\" x 14'0\"\nEn-Suite Bathroom", fill=(60, 20, 80))

    # Bedroom 2 (Bottom Left)
    d.rectangle([60, 540, 500, 700], fill=(240, 245, 250), outline=(30, 40, 60), width=3)
    d.text((200, 600), "BEDROOM 2 (GUEST SUITE)\n14'0\" x 12'0\"\nAttached Bath", fill=(20, 40, 60))

    # Bedroom 3 (Bottom Center-Right)
    d.rectangle([520, 560, 940, 700], fill=(240, 245, 250), outline=(30, 40, 60), width=3)
    d.text((660, 610), "BEDROOM 3 (KIDS ROOM)\n13'0\" x 12'0\"", fill=(20, 40, 60))

    img.save(str(floor_plan_path), "JPEG", quality=90)
    print(f"Created: floor_plan_3bhk_layout.jpg ({floor_plan_path.stat().st_size:,} bytes)")

def generate_fallback_image(path: Path, filename: str, desc: str):
    img = Image.new("RGB", (800, 600), color=(220, 225, 235))
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, 760, 560], outline=(50, 70, 100), width=4)
    d.text((80, 100), filename, fill=(20, 40, 80))
    d.text((80, 160), desc, fill=(40, 60, 90))
    img.save(str(path), "JPEG", quality=85)

if __name__ == "__main__":
    print("=" * 70)
    print("BUILDING DOMAIN-ALIGNED REAL ESTATE DATASET FOR ASSETLENS")
    print("=" * 70)
    create_real_estate_pdfs()
    create_testimonial_video()
    download_and_generate_themed_images()
    print("\nDataset generation finished successfully!")
