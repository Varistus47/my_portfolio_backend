"""Portfolio API.

Run with:
    .\\.venv\\Scripts\\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

Public GET endpoints serve the portfolio; every mutating endpoint requires the
`X-Admin-Token` header obtained from POST /api/admin/login.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import CORS_ORIGINS, UPLOAD_DIR
from database import init_db
from routers import admin, education, experience, portfolio, profile, projects, skills

app = FastAPI(
    title="Portfolio API",
    version="1.0.0",
    description="Database-backed content for the portfolio site.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    # Header-based token, not cookies. `True` combined with a wildcard header
    # list is rejected outright by browsers.
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],  # covers X-Admin-Token
    expose_headers=["Content-Disposition"],  # so JS can read the download name
)

init_db()

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

for router in (
    admin.router,
    portfolio.router,
    profile.router,
    skills.router,
    projects.router,
    education.router,
    experience.router,
):
    app.include_router(router)


@app.get("/api/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"message": "Portfolio API", "docs": "/docs"}
