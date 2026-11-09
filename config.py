"""Configuration loaded from the .env file sitting next to this module."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _path(env_key: str, default: str) -> Path:
    """Resolve a path from env, relative to BASE_DIR when not absolute."""
    raw = os.getenv(env_key, default)
    candidate = Path(raw)
    return candidate if candidate.is_absolute() else BASE_DIR / candidate


ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "stusghtyai")
TOKEN_SECRET = os.getenv("TOKEN_SECRET", "insecure-dev-secret-change-me")
TOKEN_TTL_SECONDS = int(os.getenv("TOKEN_TTL_SECONDS", "43200"))  # 12 hours

DB_PATH = _path("DB_PATH", "portfolio.db")
UPLOAD_DIR = _path("UPLOAD_DIR", "uploads")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173",
    ).split(",")
    if origin.strip()
]

MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MB
CHUNK_SIZE = 1024 * 1024  # 1 MB streaming chunks

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".avif"}
PDF_EXTENSIONS = {".pdf"}

# Created eagerly so a fresh checkout works with no manual step.
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
