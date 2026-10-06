import os
from pathlib import Path

# Base Paths (supports local and Render Persistent Disks)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", BASE_DIR / "storage"))
CERTIFICATES_DIR = STORAGE_DIR / "certificates"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)

# Database Configuration (auto-converts legacy Render postgres:// to postgresql:// for SQLAlchemy)
raw_db_url = os.getenv("DATABASE_URL")
if raw_db_url:
    if raw_db_url.startswith("postgres://"):
        DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
    else:
        DATABASE_URL = raw_db_url
else:
    DATABASE_URL = f"sqlite:///{DATA_DIR / 'certificates.db'}"

# Application Settings
APP_NAME = "Bulk Certificate Generator"
APP_VERSION = "1.0.0"
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "1000"))

# Base URL (automatically detects Render public domain if hosted on Render)
BASE_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("BASE_URL") or "http://localhost:8000"
