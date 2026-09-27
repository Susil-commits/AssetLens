import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.config import settings
from backend.database import init_db, SessionLocal
from backend.search.router import router as search_router
from backend.ingestion.router import router as ingestion_router

# Suppress Windows asyncio [WinError 10054] ConnectionResetError.
# This fires every time a browser closes a TCP connection mid-stream while
# seeking video (it drops the old Range request and opens a new one).
# It is expected behaviour during video streaming, not a real error.
class _SuppressWinError10054(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "10054" not in (record.getMessage())

for _logger_name in ("asyncio", "uvicorn.error"):
    logging.getLogger(_logger_name).addFilter(_SuppressWinError10054())


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    # ── Suppress [WinError 10054] from video range-request streaming ─────────
    # asyncio's ProactorEventLoop prints ConnectionResetError(10054) to stderr
    # via its internal callback system — it bypasses Python's logging module,
    # so a logging.Filter has no effect.  The correct fix is a custom event-loop
    # exception handler.  WinError 10054 fires every time a browser closes an
    # old TCP connection to open a new Range request while seeking in a video.
    # That is expected HTTP behaviour, not a real error.
    loop = asyncio.get_event_loop()
    _orig_handler = loop.get_exception_handler()

    def _suppress_win10054(loop, context):
        exc = context.get("exception")
        if isinstance(exc, ConnectionResetError) and getattr(exc, "winerror", None) == 10054:
            return  # silently ignore
        if callable(_orig_handler):
            _orig_handler(loop, context)
        else:
            loop.default_exception_handler(context)

    loop.set_exception_handler(_suppress_win10054)
    # ─────────────────────────────────────────────────────────────────────────

    # Startup: ensure tables and dirs exist
    init_db()

    # Mark any stale RUNNING index runs as FAILED.
    from backend.models import IndexRun
    from backend.models import utc_now
    db = SessionLocal()
    try:
        stale_runs = db.query(IndexRun).filter(IndexRun.status == "RUNNING").all()
        for run in stale_runs:
            run.status = "FAILED"
            run.error_summary = "Server restarted while indexing was in progress."
            run.completed_at = utc_now()
        if stale_runs:
            db.commit()
    finally:
        db.close()

    yield
    # Shutdown logic if any


app = FastAPI(
    title="AssetLens API",
    description="Multimodal Digital Asset Management & Natural-Language Search",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(search_router)
app.include_router(ingestion_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount thumbnails and media folders for direct previews
settings.ensure_directories()
app.mount("/api/thumbnails", StaticFiles(directory=str(settings.THUMBNAILS_DIR)), name="thumbnails")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "AssetLens",
        "device": settings.get_resolved_device(),
        "database": settings.DB_PATH.exists(),
        "version": "1.0.0"
    }

# Chrome DevTools probes this path on every page load.
# A middleware handles it BEFORE StaticFiles can return a 404 for the .json extension.
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class ChromeDevToolsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path == "/.well-known/appspecific/com.chrome.devtools.json":
            return JSONResponse({})
        return await call_next(request)

app.add_middleware(ChromeDevToolsMiddleware)

# Mount production frontend build if available
frontend_dist = settings.DATA_DIR.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
