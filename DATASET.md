# AssetLens — Media Dataset Documentation

This document describes the multimodal dataset indexed and evaluated by **AssetLens**.

---

## 1. Dataset Overview

AssetLens is benchmarked on a **programming education, real-estate, nature, and academic research dataset** spanning **3 core modalities** across **233 indexed assets totalling ~4.34 GB**:

- **Images (62 files)**: High-resolution CC0 photographs spanning residential interiors (living rooms, bedrooms, kitchens, home offices), real estate exteriors (aerial, rooftop, garden), active construction sites (workers, scaffolding, cranes), nature/landscapes (mountains, beaches, forests), people/lifestyle (yoga, chef, scientist), technology (servers, drones), animals, food, and urban cityscapes.
- **Videos (133 files, MP4)**: Dynamic educational and cinematic footage combining visual keyframe sampling and speech transcription:
  - **Programming Tutorial Series** (~110 videos, ~4.0 GB): Spoken C++, Java, and Python instructional content with rich transcribable dialogue covering operators, loops, conditionals, data types, and algorithm concepts.
  - **Open Movie Collection** (Blender Foundation CC BY): *Big Buck Bunny*, *Elephants Dream*, *Sintel Trailer* — animated films featuring outdoor environments and characters.
  - **Domain Benchmark Videos** (3 files): Custom spoken customer testimonial with dialogue, active construction site footage, and outdoor pedestrian motion.
  - **Nature & Aerial Footage** (Pexels free license, up to 4K): Wildlife documentary, aerial landscapes, urban scenes.
- **Documents (38 files, multi-page PDF)**: Spanning academic research, real-estate marketing, and computer science education materials.
- **Duplicates**: 29 video files detected as cross-folder SHA-256 duplicates; marked `DUPLICATE` in catalog with zero redundant embedding compute.

### Summary Metrics

| Modality | Indexed Files | Duplicates | Visual Chunks | Text / Transcript Chunks | Storage Size |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Images** | 62 | 0 | 62 (SigLIP 768d) | — | ~20.5 MB |
| **Videos** | 104 | 29 | 519 (SigLIP 768d keyframes) | 11,868 (faster-whisper + MiniLM 384d) | ~4,394.6 MB |
| **Documents (PDF)** | 38 | 0 | 405 (SigLIP 768d page renders) | 488 (MiniLM 384d + FTS5 BM25) | ~28.6 MB |
| **Total** | **204 indexed + 29 dup = 233** | **29** | **986 visual embeddings** | **12,356 text embeddings** | **~4.34 GB** |

*Total Content Chunks: **13,342*** (986 visual frame/page/image chunks + 12,356 dense text and speech transcript chunks).

> **Note**: Exact chunk counts depend on video duration, keyframe deduplication, and PDF page count. Re-run `python scripts/reindex_all.py` after adding files to refresh live counts from the catalog.

---

## 2. File Inventory & Specifications

### 2.1 Image Collection (`data/media/images/`)

All 62 images are verified RGB JPEG files representing distinct visual and marketing concepts. Key images relevant to the search evaluation benchmark:

| Filename | Resolution | Primary Visual Concept |
| :--- | :--- | :--- |
| `modern_living_room_luxury.jpg` | 800×533 | Luxury contemporary living room with designer sofa and glass windows |
| `living_room_interior.jpg` | 800×533 | Modern interior decor with yellow armchair, sofa, and wall art |
| `floor_plan_3bhk_layout.jpg` | 1000×750 | Architectural floor plan of a 3 BHK apartment with room dimensions |
| `residential_swimming_pool_amenity.jpg` | 800×533 | Olympic residential swimming pool with sun loungers |
| `residential_clubhouse_gym.jpg` | 800×533 | Modern residential fitness center and gym equipment |
| `residential_building_construction.jpg` | 800×533 | Multi-story apartment towers under construction with scaffolding |
| `construction_site_crane.jpg` | 800×533 | Industrial construction site with tower cranes and safety workers |
| `family_discussing_home_purchase.jpg` | 800×533 | Family reviewing home purchase agreements and keys |
| `master_bedroom_interior.jpg` | 800×533 | Elegant master bedroom interior with wood styling |
| `modern_kitchen.jpg` | 800×533 | Contemporary kitchen interior with island and bar stools |
| `residential_balcony_skyline_view.jpg` | 800×533 | High-rise residential balcony overlooking urban skyline |
| `woman_standing_with_cat.jpg` | 800×1200 | Woman standing outdoors with a domestic tabby cat *(assignment query)* |
| `woman_holding_cat.jpg` | 800×600 | Close-up of a domestic cat held by a person |
| `business_meeting.jpg` | 800×533 | Professional team collaborating around boardroom table |
| `dog_playing_park.jpg` | 800×533 | Golden retriever dog playing on green grass |
| `mountain_lake_landscape.jpg` | 800×533 | Snow-capped alpine mountain reflection over crystal lake |
| `tropical_beach_ocean.jpg` | 800×533 | Turquoise ocean waters and palm trees on sand |
| *(+ 45 additional CC0 images)* | various | Nature, food, animals, technology, people, urban cityscapes |

### 2.2 Video Collection (`data/media/videos/`)

133 MP4 files sampled for visual keyframes (OpenCV, 4-second interval with histogram-based deduplication) and speech dialogue (`faster-whisper` base int8). Organised into 4 groups:

#### Group A — Programming Tutorial Series (~110 videos, ~4.0 GB)

Spoken educational lectures covering C++, Java, and Python programming fundamentals. Rich transcribable dialogue makes these the primary driver of the 11,868 speech transcript chunks.

| Sub-series | Topics Covered | Est. Video Count |
| :--- | :--- | :--- |
| C++ Fundamentals | Boilerplate, operators, data types, type casting, namespaces | ~30 |
| Java Fundamentals | Output, variables, data types, input, control flow | ~20 |
| Control Flow (C++/Java) | if/else, switch, for/while/do-while loops, break/continue | ~35 |
| Patterns & Practice | Number patterns, prime check, interest calculator, algorithms | ~25 |

#### Group B — Benchmark Domain Videos (3 videos)

| Filename | Duration | Keyframes | Speech Segments | Primary Scene |
| :--- | :--- | :--- | :--- | :--- |
| `customer_home_purchase_testimonial.mp4` | 40.8s | 1 | **9 speech segments** | Customer on camera reviewing 3 BHK purchase at Greenwood Heights Phase 2 |
| `construction_worker_zone.mp4` | 33.6s | 8 | — | Active construction site, machinery, workers in hi-vis safety gear |
| `people_walking_outdoors.mp4` | 36.3s | 9 | — | Pedestrians along urban city sidewalks |

#### Group C — Open Movie Collection (Blender Foundation CC BY)

| Filename | Description |
| :--- | :--- |
| `big_buck_bunny_720p.mp4` | Animated short — forest animals, outdoor environment |
| `elephants_dream_720p.mp4` | Surreal animated short film |
| `sintel_trailer.mp4` | Fantasy outdoor animated trailer |

#### Group D — Nature & Aerial Footage (Pexels free license)

| Filename | Description |
| :--- | :--- |
| `nature_wildlife_documentary.mp4` | Wildlife footage — animals in natural habitat |
| `13723493_3840_2160_60fps.mp4` | 4K aerial landscape footage |
| `14433607_3840_2160_60fps.mp4` | 4K aerial landscape footage |
| *(+ additional Pexels 4K clips)* | Urban, aerial, outdoor scenes at various resolutions |

### 2.3 Document Collection (`data/media/documents/`)

38 multi-page PDF files processed via PyMuPDF dual-pipeline (visual page rendering → SigLIP 768d + sliding-window text chunking → MiniLM 384d + SQLite FTS5 BM25). Organised into 4 groups:

#### Group A — Real-Estate Benchmark Brochures (3 files)

| Filename | Pages | Key Content |
| :--- | :--- | :--- |
| `greenwood_heights_residential_brochure.pdf` | 4 | 3 BHK configurations (2,150 sq ft), Olympic pool, gym, Q4 2026 possession |
| `skyline_towers_floor_plans.pdf` | 3 | High-rise tower master plan, Type A 3 BHK dimensions, rooftop sky lounge |
| `oakridge_sanctuary_community_brochure.pdf` | 3 | 3 BHK/4 BHK garden suites, resort lagoon pool, wellness spa |

#### Group B — Academic Research Papers (5 files)

| Filename | Topic |
| :--- | :--- |
| `attention_is_all_you_need.pdf` | Transformer architecture, self-attention mechanisms |
| `deep_residual_learning_resnet.pdf` | ResNet deep residual networks |
| `bert_pretraining_nlp.pdf` | BERT pre-training for NLP |
| `generative_adversarial_nets.pdf` | GAN fundamentals |
| `clip_visual_models.pdf` | CLIP visual-language pre-training |

#### Group C — CS & Data Science Notes / Guides (7 files)

| Filename | Topic |
| :--- | :--- |
| `Computer Networks Notes.pdf` | Networking fundamentals |
| `DBMS Notes.pdf` | Database management systems |
| `Operating System Notes.pdf` | OS concepts |
| `WEB SCAPING NOTES.pdf` | Web scraping techniques |
| `DATA VISUALISATION - MATPLOTLIB .pdf` | Matplotlib visualization guide |
| `DATA VISUALISATION - SEABORN .pdf` | Seaborn visualization guide |
| `06. Space and Time Complexity.pdf` | Algorithm complexity analysis |

#### Group D — Programming Q&A Worksheets (23 files)

Problem sets and answer sheets covering arrays, binary numbers, conditionals, operators, pointers, sorting, functions, patterns, loops, and variables. Includes `FBL_PassItOn_Stories_Volume_2.pdf` (general text document).

---

## 3. Directory Layout & Storage Architecture

```
AssetLens/
├── data/
│   ├── media/                   # Source raw assets (strictly gitignored)
│   │   ├── images/              # 62 image files (.jpg, ~20.5 MB)
│   │   ├── videos/              # 133 video files (.mp4, ~4.39 GB)
│   │   └── documents/           # 38 document files (.pdf, ~28.6 MB)
│   ├── derived/
│   │   └── thumbnails/          # Generated preview thumbnails (aspect-fit JPEG)
│   └── db/
│       ├── catalog.sqlite       # SQLite (assets, content_chunks, index_runs, FTS5 table)
│       └── lancedb/             # Embedded LanceDB columnar vector storage
│           ├── visual_embeddings.lance/   # ~986 SigLIP 768d vectors
│           └── text_embeddings.lance/    # ~12,356 MiniLM 384d text & transcript vectors
```

---

## 4. Search Evaluation Dataset

The search quality evaluation (`evaluation/report.md`) was performed on a curated **31-asset benchmark subset** extracted from the full catalog — specifically chosen to have clear, verifiable ground-truth labels:

- **25 Images**: Residential interiors, construction sites, floor plans, lifestyle, animals.
- **3 Videos**: Customer testimonial (with transcribable speech), construction zone, pedestrian motion.
- **3 PDFs**: Three real-estate brochures with specific, measurable text content.

This subset yielded **72 content chunks** (53 visual, 19 text/speech) and supported **13 test queries** covering all 5 literal assignment example queries plus cross-modal, fine-grained, and out-of-domain edge-case scenarios.

> **Why a curated benchmark subset?** Evaluating retrieval quality requires knowing the ground truth for every query in advance. The 31-asset subset provides exact labels for honest Precision@1/P@5/MRR measurement. The full 233-asset catalog demonstrates system scale and real-world robustness.

---

## 5. Scalability & Production Readiness

| Component | Scaling Behaviour |
| :--- | :--- |
| **Incremental Scanner** (`mtime` + `size_bytes` fingerprint) | Re-scans a 10,000-file folder in seconds; only new or modified files hit the embedding pipeline |
| **SHA-256 Streaming Hasher** (64 KB chunks) | Constant memory usage regardless of file size; identifies cross-folder duplicates with zero redundant embedding compute |
| **LanceDB Embedded Columnar Store** | Handles tens of millions of 768-dim vectors on disk with sub-10 ms cosine ANN queries via IVF-PQ indexing |
| **SQLite FTS5 BM25 Index** | Handles multi-GB databases efficiently; scales to millions of text chunks with WAL mode |
| **Background Threading with Lock** | `threading.Thread` + `_INDEX_LOCK` design supports overnight batch jobs without blocking the API server |
| **Per-Asset Fault Isolation** | Each asset's `try/except` block means a single corrupt 4 GB video cannot stall the rest of the queue |
| **Retry API** (`/api/index/retry-failed`) | Failed assets retried in isolation without re-scanning the entire collection |

For collections exceeding ~100,000 assets:
1. Replace `threading.Thread` with a Celery or RQ task queue for distributed worker scaling.
2. Enable LanceDB's IVF-PQ approximate nearest-neighbour index for sub-linear query time at millions of vectors.
3. Partition SQLite FTS5 by modality or date shard to keep the full-text index warm.

---

## 6. Licenses & Attribution

- **Images**: Sourced from Unsplash under the **Unsplash Free License** / **Creative Commons CC0**, permitting unrestricted personal and commercial use.
- **Videos**: Programming tutorial content (educational fair-use); Blender Foundation movies under **CC BY 3.0**; nature/aerial footage under **Pexels Free License**; benchmark domain videos are original synthesized content.
- **Documents**: Academic papers are open-access arXiv publications. Real-estate brochures created specifically for the AssetLens benchmark evaluation. CS notes are personal study materials included for search evaluation purposes only.
