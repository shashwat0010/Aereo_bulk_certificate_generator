import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = BASE_DIR / "storage"
CERTIFICATES_DIR = STORAGE_DIR / "certificates"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'certificates.db'}")

# Application Settings
APP_NAME = "Bulk Certificate Generator"
APP_VERSION = "1.0.0"
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "1000"))
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
