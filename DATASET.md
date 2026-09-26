# AssetLens — Media Dataset Documentation

This document describes the benchmark multimodal dataset curated and indexed by **AssetLens**.

---

## 1. Dataset Overview

AssetLens ships with a local multimodal dataset covering **3 core modalities**:
- **Images (17 files)**: High-resolution real-world photos covering varied scenes, animals, indoor environments, industrial sites, food, and people.
- **Videos (2 files, MP4)**: Dynamic temporal video footage capturing realistic motion (pedestrians in urban sidewalk environments and industrial construction zones).
- **Documents (3 files, multi-page PDF)**: Landmark scientific papers containing both rich technical text and architectural diagrams/plots.

### Summary Metrics
| Modality | File Count | Extracted Visual Chunks | Extracted Text Chunks | Storage Size |
| :--- | :--- | :--- | :--- | :--- |
| **Images** | 17 | 17 (SigLIP 768d) | — | ~1.4 MB |
| **Videos** | 2 | 17 (SigLIP 768d keyframes) | — | ~18.1 MB |
| **Documents (PDF)** | 3 (41 pages) | 41 (SigLIP 768d page renders) | 80 (MiniLM 384d + FTS5) | ~4.0 MB |
| **Total** | **22 files** | **75 visual chunks** | **80 text chunks** | **~23.5 MB** |

---

## 2. File Inventory & Specifications

### 2.1 Image Collection (`data/media/images/`)
All images are verified RGB JPEG files with diverse visual concepts:

| Filename | Resolution | Dimensions | Primary Visual Concept |
| :--- | :--- | :--- | :--- |
| `woman_standing_with_cat.jpg` | 84 KB | 800x1200 | Woman standing outdoors with a domestic tabby cat |
| `woman_holding_cat.jpg` | 45 KB | 800x600 | Close-up of a domestic cat held by a person |
| `living_room_interior.jpg` | 67 KB | 800x533 | Modern interior decor with yellow chair, sofa, wall art |
| `modern_kitchen.jpg` | 81 KB | 800x533 | Sleek contemporary kitchen with island and bar stools |
| `sports_car_red.jpg` | 52 KB | 800x533 | Red sports coupe car driving on asphalt road |
| `coffee_latte_art.jpg` | 152 KB | 800x533 | Hot cup of cappuccino with delicate foam leaf latte art |
| `delicious_pasta_dish.jpg` | 88 KB | 800x533 | Gourmet Italian pasta dish served with sauce and basil |
| `hospital_doctor_stethoscope.jpg` | 74 KB | 800x533 | Medical doctor in scrubs with stethoscope in clinic |
| `construction_site_crane.jpg` | 146 KB | 800x533 | Construction worker with safety helmet and tower cranes |
| `dog_playing_park.jpg` | 159 KB | 800x533 | Golden retriever dog playing on green grass in park |
| `acoustic_guitar_player.jpg` | 36 KB | 800x533 | Musician playing acoustic guitar strings close-up |
| `airplane_flying_clouds.jpg` | 48 KB | 800x533 | Commercial jet airliner cruising above white cloud cover |
| `business_meeting.jpg` | 64 KB | 800x533 | Professional team collaborating around boardroom table |
| `mountain_lake_landscape.jpg` | 121 KB | 800x533 | Snow-capped alpine mountain reflection over crystal lake |
| `snowy_winter_forest.jpg` | 73 KB | 800x533 | Pine forest blanketed in deep winter snow |
| `tropical_beach_ocean.jpg` | 65 KB | 800x533 | Turquoise ocean waters and palm trees on sand |
| `vintage_camera_photo.jpg` | 30 KB | 800x533 | Retro 35mm rangefinder analog film camera |

### 2.2 Video Collection (`data/media/videos/`)
Temporal video sequences sampled with OpenCV at 4-second intervals with duplicate-frame elimination:

| Filename | Duration | Framerate | Resolution | Extracted Keyframes | Keyframe Timestamps | Primary Scene |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `construction_worker_zone.mp4` | 33.6s | 25 fps | 1280x720 | 8 keyframes | 0s, 4s, 8s, 12s, 16s, 20s, 24s, 28s | Active construction site, machinery, workers in hi-vis gear |
| `people_walking_outdoors.mp4` | 36.3s | 25 fps | 1280x720 | 9 keyframes | 0s, 4s, 8s, 12s, 16s, 20s, 24s, 28s, 32s | Pedestrians walking outdoors on urban sidewalk |

### 2.3 Document Collection (`data/media/documents/`)
Seminal computer science papers processed using PyMuPDF (fitz) dual-pipeline (page layout visual rendering + dense sliding-window text chunking + SQLite FTS5 BM25):

| Filename | Page Count | Text Chunks | Topic & Key Sections |
| :--- | :--- | :--- | :--- |
| `transformer_attention_paper.pdf` | 15 pages | 20 chunks | "Attention Is All You Need" (Vaswani et al.) — Multi-Head Attention, Scaled Dot-Product, Positional Encodings |
| `deep_residual_learning_paper.pdf` | 12 pages | 25 chunks | "Deep Residual Learning for Image Recognition" (He et al.) — ResNet, Residual Blocks, Degradation problem |
| `tracemonkey_compiler_paper.pdf` | 14 pages | 35 chunks | "Trace-based Just-in-Time Type Specialization for Dynamic Languages" (Gal et al.) — SpiderMonkey/TraceMonkey JIT |

---

## 3. Directory Layout & Storage Architecture

```
AssetLens/
├── data/
│   ├── media/                  # Source raw assets (strictly gitignored)
│   │   ├── images/             # 17 image files (.jpg, .png)
│   │   ├── videos/             # 2 temporal video files (.mp4)
│   │   └── documents/          # 3 technical PDF research papers (.pdf)
│   ├── derived/
│   │   └── thumbnails/         # Generated preview thumbnails (320px cover, 480px keyframe/pages)
│   └── db/
│       ├── catalog.sqlite      # SQLite database (assets, content_chunks, index_runs, FTS5 table)
│       └── lancedb/            # Embedded LanceDB columnar vector storage
│           ├── visual_embeddings.lance/ (768-dim SigLIP vectors)
│           └── text_embeddings.lance/   (384-dim all-MiniLM-L6-v2 vectors)
```

---

## 4. Licenses & Attribution

- **Images**: Sourced from Unsplash and Wikimedia Commons under the **Unsplash Free License** / **Creative Commons CC0 (Public Domain)**, permitting unrestricted commercial and personal use with no copyright restrictions.
- **Videos**: Sourced from Pexels under the **Pexels Free License**, authorizing free use, modification, and reproduction.
- **Documents**: Landmark open-access preprints published on **arXiv.org** under standard arXiv open-access academic distribution licenses:
  - *Vaswani et al., 2017* (arXiv:1706.03762)
  - *He et al., 2015* (arXiv:1512.03385)
  - *Gal et al., 2009* (ACM SIGPLAN PLDI)
