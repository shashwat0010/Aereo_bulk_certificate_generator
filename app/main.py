import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import APP_NAME, APP_VERSION, BASE_DIR
from app.database import Base, engine
from app.api.routes import router as api_router
from app.api.web import web_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("bulk_certificate_generator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB schema tables exist
    logger.info("Initializing relational database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info(f"{APP_NAME} v{APP_VERSION} initialized successfully.")
    yield
    # Shutdown
    logger.info("Application shutting down.")


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Scalable backend API for high-volume bulk certificate generation with background tracking, error isolation, and verification.",
    lifespan=lifespan
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets
static_path = BASE_DIR / "app" / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include Routers
app.include_router(web_router)
app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": APP_NAME,
        "version": APP_VERSION
    }
