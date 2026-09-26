from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.config import settings
from backend.database import init_db
from backend.search.router import router as search_router
from backend.ingestion.router import router as ingestion_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables and dirs exist
    init_db()
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

# Mount production frontend build if available
frontend_dist = settings.DATA_DIR.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
