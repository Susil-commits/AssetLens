# AssetLens — Agent Execution Plan

You are building **AssetLens**, a local multimodal Digital Asset Management system with natural-language search over images, videos, and PDFs. The full requirements are in the attached master specification — treat that as the source of truth for *what* to build. This document tells you the **order** to build it in, and the **gates** you must pass before moving to the next phase.

## Non-negotiable rules

- Work phase by phase, in order. Do not start a phase until the previous phase's gate criteria are met.
- Never use mocked embeddings, hardcoded search results, or placeholder functions (`pass`, `TODO`, `return []`) for anything in the "must work" list below.
- After each phase, run the tests for that phase and fix failures before continuing. Report status before moving on.
- If a dependency's API differs from what's expected, check current docs and adapt — don't guess outdated syntax.
- If short on time, cut scope by *documenting a limitation*, not by faking a feature. Video processing is the first thing to scope down if needed (see Phase 4 fallback).
- Do not touch frontend (Phase 7) until Phase 5 (hybrid search API) is verified working via curl/script, not just "code compiles."

---

## Phase 0 — Skeleton
**Build:**
- Repo structure per spec section 6 (backend/frontend/data/evaluation/scripts/docs).
- `config.py` reading `.env`, with `DEVICE=auto` → auto-detect CUDA vs CPU.
- FastAPI app with `/health` endpoint.
- SQLAlchemy models + table creation for `assets`, `content_chunks`, `index_runs` (spec section 7).

**Gate to pass before continuing:**
- `uvicorn` boots without error.
- Tables exist in `data/db/catalog.sqlite` (verify with a query, not just "no crash").

---

## Phase 1 — Scanner + hashing + dedup foundation
**Build:**
- `ingestion/scanner.py`: recursive scan, classify by extension (image/video/pdf/unsupported).
- `ingestion/hasher.py`: SHA-256 per file.
- Incremental-skip logic: compare (path, size, mtime) against DB; skip unchanged.
- Insert discovered files into `assets` with status `DISCOVERED` → `PENDING`.
- `tests/test_scanner.py`, `tests/test_hashing.py`, `tests/test_deduplication.py`.

**Gate to pass before continuing:**
- Tests pass.
- Running the scanner twice on the same folder reprocesses nothing the second time.
- A file with identical hash to an existing asset is marked `DUPLICATE`, not reprocessed.

---

## Phase 2 — Image pipeline (build first — cheapest full-loop validation)
**Build:**
- `ai/model_manager.py`: load SigLIP2 once, expose `encode_image()` / `encode_text_for_visual_search()`, normalized embeddings.
- `processors/image_processor.py`: metadata → thumbnail → SigLIP embed → write to LanceDB + `content_chunks` (chunk_type=IMAGE).
- A standalone script (`scripts/dev_image_search_check.py` or similar) that indexes a small folder of real images and runs a text query against LanceDB, printing ranked filenames + scores.

**Gate to pass before continuing — do not skip this checkpoint:**
- Index ~15 varied real images (not synthetic/placeholder).
- Run at least 3 plain-English queries against them.
- Confirm top results are visually correct (e.g., "a person outdoors" actually returns outdoor photos, not filename matches).
- If this doesn't work, stop and debug before adding PDF/video — everything downstream depends on this loop being real.

---

## Phase 3 — PDF pipeline
**Build:**
- `processors/pdf_processor.py`: PyMuPDF text extraction per page, 300–800 word chunks, BGE-M3 embed. OCR only as fallback when extracted text is near-empty.
- Page rendering → SigLIP visual embed per page.
- Store `content_chunks` rows (PDF_TEXT, PDF_PAGE, PDF_OCR as needed).

**Gate to pass before continuing:**
- Index 2–3 real PDFs/brochures.
- A query for specific text known to be in one PDF (e.g., a phrase or spec term) returns the correct page.
- A query for something only visually present (not in extracted text) still surfaces the right page via the visual embedding path.

---

## Phase 4 — Video pipeline
**Build:**
- Frame sampling per spec section 11 rules (interval by duration, first/middle/last, dedupe near-identical frames), SigLIP embed per sampled frame with timestamp.
- FFmpeg audio extraction → faster-whisper → timestamped transcript segments → BGE-M3 embed per segment.

**Fallback if time-constrained:** ship frame-based visual search only, skip transcription, and document this explicitly in known limitations — do not silently omit it.

**Gate to pass before continuing:**
- Index 2 short real videos.
- A visual query (e.g., "construction activity") returns the video with a matched timestamp.
- If transcription is implemented: a spoken-content query (e.g., "testimonial") returns the video via transcript match, with timestamp.

---

## Phase 5 — Hybrid search + fusion
**Build:**
- `search/visual_search.py`, `text_search.py` (BGE-M3 over PDF/transcript/OCR chunks), `keyword_search.py` (SQLite FTS5).
- `search/fusion.py`: RRF-based combination, weights configurable (start: visual 0.50 / text 0.35 / keyword 0.15).
- `search/ranking.py`: aggregate chunk-level hits to one result per parent asset, carrying best score + best timestamp/page.
- `GET /api/search` per spec section 20 response shape, including `matched_sources` and a "why this matched" explanation built from real retrieval data (never hardcoded).
- Minimum similarity threshold — return "no sufficiently relevant results" instead of padding with weak matches.

**Gate to pass before continuing — verify via curl/script before frontend work:**
- Run at least 5 of the spec's example queries (spanning image, PDF, video if implemented) directly against the API.
- Confirm ranking is sane and no duplicate chunk-level entries appear for the same asset.

---

## Phase 6 — Reliability
**Build:**
- Per-asset try/except in the processing loop → mark `FAILED` with a structured error category (spec section 46), log it, continue to next file — one bad file must never kill the run.
- `POST /api/index/retry-failed` reprocesses only failed assets.
- `INDEX_SCHEMA_VERSION` / `EMBEDDING_VERSION` fields stored per chunk (even if a rebuild trigger isn't fully wired up).
- `POST /api/index/start` (non-blocking, returns run ID) + `GET /api/index/status` (real progress, not simulated).

**Gate to pass before continuing:**
- Deliberately include one corrupted/unsupported file in the test folder; confirm the run completes with it marked `FAILED`/`UNSUPPORTED` and everything else still processes.
- Retry-failed only touches the failed asset.

---

## Phase 7 — Frontend
**Build:**
- React + Vite dashboard: search bar, type filters (All/Images/Videos/PDFs), result grid with thumbnail/filename/type/relevance/location/match info, preview modal (image/video-with-seek/PDF-page), index progress panel polling `/api/index/status`.
- Keep styling plain — this is the lowest engineering priority per the spec.

**Gate to pass before continuing:**
- Full user flow works end to end: start indexing → watch real progress → search → filter → preview → see original path.

---

## Phase 8 — Evaluation
**Build:**
- `evaluation/queries.json`: 10–15 queries across visual / text-document / video-transcript / cross-modal categories (spec section 41).
- Run each against the real indexed dataset, manually judge relevance, compute Precision@5 / Recall@10 / MRR.
- `evaluation/report.md` per spec section 43 — include actual failures, not just successes.

**Gate to pass before continuing:**
- Every query in the file has been run against the real system, not pre-filled with assumed results.

---

## Phase 9 — Docs and final pass
**Build:**
- README covering everything in spec section 51 (architecture, models, why each model, data flow, setup, env vars, run/test/eval instructions, limitations, production improvements).
- `DATASET.md` describing sources, licenses, counts, size.
- `.gitignore` excluding `data/media`, `data/derived`, `data/db`.
- Final honest pass on known limitations (section 66) and production improvements (section 67) — write what's actually true of *this* build, not generic boilerplate.

**Gate — final acceptance check:**
- Walk through the acceptance criteria checklist in spec section 64 item by item and report which are met, which are partial, and which were deliberately scoped out and why.

---

## Reporting format after each phase

After completing each phase, report:
1. What was built (files/modules touched).
2. What was tested and the actual result (not "should work").
3. Any deviation from the spec and why.
4. Whether the gate criteria above are met — if not, fix before proceeding.

At the very end, produce the final engineering report described in spec section 70: what was implemented, what was tested, dataset statistics, evaluation results, known limitations, how to run it.
