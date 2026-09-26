import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
import torch

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    DEVICE: str = "auto"
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = BASE_DIR / "data" / "db" / "catalog.sqlite"
    LANCEDB_URI: Path = BASE_DIR / "data" / "db" / "lancedb"
    MEDIA_DIR: Path = BASE_DIR / "data" / "media"
    DERIVED_DIR: Path = BASE_DIR / "data" / "derived"
    THUMBNAILS_DIR: Path = BASE_DIR / "data" / "derived" / "thumbnails"

    SIGLIP_MODEL_NAME: str = "google/siglip-base-patch16-224"
    TEXT_EMBED_MODEL_NAME: str = "BAAI/bge-m3"

    SIMILARITY_THRESHOLD: float = 0.15
    INDEX_SCHEMA_VERSION: int = 1
    EMBEDDING_VERSION: str = "v1.0"

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    def get_resolved_device(self) -> str:
        if self.DEVICE.lower() == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return self.DEVICE.lower()

    def ensure_directories(self) -> None:
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.LANCEDB_URI.mkdir(parents=True, exist_ok=True)
        self.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        self.DERIVED_DIR.mkdir(parents=True, exist_ok=True)
        self.THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
