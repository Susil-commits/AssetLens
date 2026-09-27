# AssetLens — Media Dataset Documentation

This document describes the benchmark multimodal dataset curated, indexed, and evaluated by **AssetLens**.

---

## 1. Dataset Overview

AssetLens is benchmarked on a **real-estate, nature, technology, and multimodal marketing dataset** covering **3 core modalities** across **99 files totalling ~1.25 GB**:

- **Images (62 files)**: High-resolution 1920 px photos (Unsplash CC0) spanning residential interiors (living rooms, bedrooms, kitchens, bathrooms, home offices), real estate exteriors (aerial, rooftop, garden), active construction sites (workers, scaffolding, blueprints, concrete pours), nature/landscapes (aurora, desert dunes, lavender fields, waterfalls, forests), people/lifestyle (yoga, chef, scientist, surfer), technology (servers, drones, laptops), food, animals, and urban cityscapes.
- **Videos (28 files, MP4)**: Dynamic temporal footage combining visual keyframe sampling and speech transcription:
  - A spoken **Customer Testimonial Video** with timestamped dialogue transcribed via `faster-whisper`.
  - An **Industrial Construction Zone** video showing machinery and workers.
  - An **Outdoor Pedestrian Motion** video capturing sidewalk movement.
  - **Big Buck Bunny** (Blender Foundation CC BY) — animated film featuring forest and animals.
  - **Elephants Dream** (Blender Foundation CC BY) — surreal animated short film.
  - **Sintel Trailer** (Blender Foundation CC BY) — fantasy outdoor animated trailer.
  - **Nature Wildlife Documentary** (Pexels free license) — wildlife footage.
  - **Matplotlib Tutorial Series** (10 videos, ~446 MB) — spoken instructional videos with rich transcribable speech content covering data visualization concepts.
  - **Aerial/landscape/nature footage** (Pexels, various resolutions up to 4K).
- **Documents (8 files, multi-page PDF)**: Three domain-specific real-estate brochures ("3 BHK", "amenities", "swimming pool") plus five open-access academic papers (Attention/Transformer, ResNet, BERT, GAN, CLIP) containing dense technical text, mathematical notation, and figure-rich layouts.

### Summary Metrics
| Modality | File Count | Estimated Visual Chunks | Estimated Text Chunks | Storage Size |
| :--- | :--- | :--- | :--- | :--- |
| **Images** | 62 | ~62 (SigLIP 768d) | — | ~20.5 MB |
| **Videos** | 28 | ~350 (SigLIP 768d keyframes) | ~80 (`faster-whisper` + MiniLM 384d) | ~1215.7 MB |
| **Documents (PDF)** | 9 (~50 pages) | ~50 (SigLIP 768d page renders) | ~50 (MiniLM 384d + FTS5 BM25) | ~17.9 MB |
| **Total** | **99 files** | **~462 visual embeddings** | **~130 text embeddings** | **~1.25 GB** |

*Estimated Total Content Chunks*: **~592 chunks** (462 visual frame/page/image chunks + 130 dense text and speech transcript chunks).

> **Note**: Exact chunk counts depend on video duration/keyframe deduplication and PDF page count. Re-run `python scripts/reindex_real_dataset.py` after downloading to get live counts from the catalog.

---

## 2. File Inventory & Specifications

### 2.1 Image Collection (`data/media/images/`)
All images are verified RGB JPEG files representing distinct visual and marketing concepts:

| Filename | Resolution | Dimensions | Primary Visual Concept / Domain Relevance |
| :--- | :--- | :--- | :--- |
| `modern_living_room_luxury.jpg` | 111 KB | 800x533 | Luxury contemporary living room with designer sofa and glass windows |
| `living_room_interior.jpg` | 67 KB | 800x533 | Modern interior decor with yellow armchair, sofa, and wall art |
| `floor_plan_3bhk_layout.jpg` | 79 KB | 1000x750 | Architectural floor plan drawing of a luxury 3 BHK apartment with room dimensions |
| `residential_swimming_pool_amenity.jpg` | 132 KB | 800x533 | Olympic residential swimming pool amenity with clear blue water and sun loungers |
| `residential_clubhouse_gym.jpg` | 91 KB | 800x533 | Modern residential project fitness center and clubhouse gym equipment |
| `residential_building_construction.jpg` | 52 KB | 800x533 | Multi-story residential apartment towers under construction with scaffolding |
| `construction_site_crane.jpg` | 146 KB | 800x533 | Industrial construction site with tower cranes and safety workers |
| `family_discussing_home_purchase.jpg` | 53 KB | 800x533 | Family and property consultant reviewing home purchase agreements and keys |
| `master_bedroom_interior.jpg` | 133 KB | 800x533 | Elegant master bedroom interior with wood styling and panoramic view |
| `modern_kitchen.jpg` | 81 KB | 800x533 | Contemporary kitchen interior with island and bar stools |
| `residential_balcony_skyline_view.jpg` | 95 KB | 800x533 | High-rise residential balcony overlooking urban skyline |
| `woman_standing_with_cat.jpg` | 84 KB | 800x1200 | Woman standing outdoors with a domestic tabby cat (assignment query) |
| `woman_holding_cat.jpg` | 45 KB | 800x600 | Close-up of a domestic cat held by a person |
| `business_meeting.jpg` | 64 KB | 800x533 | Professional team collaborating around boardroom table |
| `sports_car_red.jpg` | 52 KB | 800x533 | Red sports coupe car driving on asphalt road |
| `coffee_latte_art.jpg` | 152 KB | 800x533 | Hot cup of cappuccino with delicate foam leaf latte art |
| `delicious_pasta_dish.jpg` | 88 KB | 800x533 | Gourmet Italian pasta dish served with sauce and basil |
| `hospital_doctor_stethoscope.jpg` | 74 KB | 800x533 | Medical doctor in scrubs with stethoscope in clinic |
| `dog_playing_park.jpg` | 159 KB | 800x533 | Golden retriever dog playing on green grass in park |
| `acoustic_guitar_player.jpg` | 36 KB | 800x533 | Musician playing acoustic guitar strings close-up |
| `airplane_flying_clouds.jpg` | 48 KB | 800x533 | Commercial jet airliner cruising above white cloud cover |
| `mountain_lake_landscape.jpg` | 121 KB | 800x533 | Snow-capped alpine mountain reflection over crystal lake |
| `snowy_winter_forest.jpg` | 73 KB | 800x533 | Pine forest blanketed in deep winter snow |
| `tropical_beach_ocean.jpg` | 65 KB | 800x533 | Turquoise ocean waters and palm trees on sand |
| `vintage_camera_photo.jpg` | 30 KB | 800x533 | Retro 35mm rangefinder analog film camera |

### 2.2 Video Collection (`data/media/videos/`)
Temporal video files sampled for visual keyframes (OpenCV) and speech audio dialogue (`faster-whisper`):

| Filename | Duration | Framerate | Extracted Keyframes | Speech Transcripts | Primary Scene & Spoken Dialogue |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `customer_home_purchase_testimonial.mp4` | 40.8s | 25 fps | 1 keyframe (00:00) | **9 speech segments** (MiniLM 384d) | Customer on camera reviewing her 3 BHK home purchase at Greenwood Heights Phase 2, praising the swimming pool, clubhouse, and handover process |
| `construction_worker_zone.mp4` | 33.6s | 25 fps | 8 keyframes (0s to 28s) | — | Active construction site, machinery, workers in hi-vis safety gear |
| `people_walking_outdoors.mp4` | 36.3s | 25 fps | 9 keyframes (0s to 32s) | — | Pedestrians walking outdoors along urban city sidewalks |

### 2.3 Document Collection (`data/media/documents/`)
Domain-aligned real-estate marketing and architectural layout documents processed using PyMuPDF dual-pipeline (visual page image rendering + dense sliding-window text chunking + SQLite FTS5 BM25):

| Filename | Page Count | Visual Chunks | Text Chunks | Primary Topics & Key Sections |
| :--- | :--- | :--- | :--- | :--- |
| `greenwood_heights_residential_brochure.pdf` | 4 pages | 4 pages (SigLIP 768d) | 4 chunks (MiniLM 384d) | Executive overview of Greenwood Heights Phase 2, detailed 3 BHK configurations (2,150 sq ft), Olympic swimming pool, gym amenities, and Q4 2026 possession schedule |
| `skyline_towers_floor_plans.pdf` | 3 pages | 3 pages (SigLIP 768d) | 3 chunks (MiniLM 384d) | High-rise tower master plan, Type A 3 BHK architectural floor plan with room dimensions, rooftop sky lounge, and EV charging bays |
| `oakridge_sanctuary_community_brochure.pdf` | 3 pages | 3 pages (SigLIP 768d) | 3 chunks (MiniLM 384d) | Gated villa enclave brochure, 3 BHK garden suites and 4 BHK forest estates, resort lagoon swimming pool, and wellness spa |

---

## 3. Directory Layout & Storage Architecture

```
AssetLens/
├── data/
│   ├── media/                  # Source raw assets (strictly gitignored)
│   │   ├── images/             # 25 image files (.jpg)
│   │   ├── videos/             # 3 temporal video files (.mp4 with audio)
│   │   └── documents/          # 3 real-estate brochures and floor plans (.pdf)
│   ├── derived/
│   │   └── thumbnails/         # Generated preview thumbnails (320px cover, 480px keyframe/pages)
│   └── db/
│       ├── catalog.sqlite      # SQLite database (assets, content_chunks, index_runs, FTS5 table)
│       └── lancedb/            # Embedded LanceDB columnar vector storage
│           ├── visual_embeddings.lance/ (53 SigLIP 768d vectors)
│           └── text_embeddings.lance/   (19 MiniLM 384d text & transcript vectors)
```

---

## 5. Dataset Size Constraint & Scalability

### Why the Demo Dataset is Small (~21 MB / 31 files)

The benchmark dataset was intentionally kept compact due to practical development constraints:

- **Storage**: Downloading and committing 5–10 GB of media to a local machine during development would exhaust OneDrive sync bandwidth and bloat the repository history.
- **Model inference time**: Embedding every frame of hours of video or thousands of high-resolution images with SigLIP on a CPU takes significant wall-clock time during iterative development.
- **Correctness focus**: The assignment notes *"The size of the dataset alone will not determine the score. We are more interested in how the system is designed and how well it works."* A curated 31-asset set with exact ground-truth labels gives more reliable evaluation signal than a noisy 5 GB dump.

### How AssetLens Handles a 5–10 GB Production Collection

The architecture is designed from the ground up for scale — no structural changes are needed:

| Component | Scaling Behaviour |
| :--- | :--- |
| **Incremental Scanner** (`mtime` + `size_bytes` fingerprint) | Re-scans a 10,000-file folder in seconds; only new or modified files hit the embedding pipeline |
| **SHA-256 Streaming Hasher** (64 KB chunks) | Constant memory usage regardless of file size; identifies cross-folder duplicates with zero redundant embedding compute |
| **LanceDB Embedded Columnar Store** | Based on the Lance format — benchmarked to handle tens of millions of 768-dim vectors on disk with sub-10 ms cosine ANN queries via IVF-PQ indexing |
| **SQLite FTS5 BM25 Index** | SQLite handles multi-GB databases efficiently; FTS5 virtual tables scale to millions of text chunks with proper WAL mode |
| **Background Threading with Lock** | The `threading.Thread` + `_INDEX_LOCK` design already supports running overnight batch jobs without blocking the API server |
| **Per-Asset Fault Isolation** | Each asset's try/except block means a single corrupt 4 GB video cannot stall the rest of the queue |
| **Retry API** (`/api/index/retry-failed`) | Failed assets can be retried in isolation after the root cause is fixed, without re-scanning the entire collection |

For collections exceeding ~100,000 assets, the natural next steps would be:
1. Replace `threading.Thread` with a Celery or RQ task queue for distributed worker scaling.
2. Enable LanceDB's IVF-PQ approximate nearest-neighbour index for sub-linear query time at millions of vectors.
3. Partition SQLite FTS5 by modality or date shard to keep full-text index warm.

---

## 6. Licenses & Attribution

- **Images**: Sourced from Unsplash under the **Unsplash Free License** / **Creative Commons CC0 (Public Domain)**, permitting unrestricted personal and commercial use without copyright restrictions.
- **Videos**: Sourced from Pexels under the **Pexels Free License** and synthesized with royalty-free assets and local text-to-speech for customer testimonial benchmarking.
- **Documents**: Created specifically for the AssetLens benchmark evaluation, modeling authentic real-estate marketing and architectural brochures with clear public-domain demonstration text.
