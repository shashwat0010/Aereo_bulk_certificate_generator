from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path
from app.config import BASE_DIR

web_router = APIRouter(tags=["UI"])

STATIC_DIR = BASE_DIR / "app" / "static"


@web_router.get("/", include_in_schema=False)
def serve_home():
    return FileResponse(STATIC_DIR / "index.html")
