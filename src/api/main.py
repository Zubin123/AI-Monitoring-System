"""FastAPI application main file."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.core import get_logger, setup_logging
from src.api.routes import health, predict
from src.api.dependencies import get_model_service

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown tasks.
    """
    # Startup
    # Setup logging first (before any other operations)
    setup_logging()
    logger.info("Starting up AI Model Monitoring API...")
    
    try:
        # Load model
        model_service = get_model_service()
        model_service.load_model()
        
        logger.info("Application startup complete")
    except Exception as e:
        logger.critical(f"Application startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(predict.router, tags=["Predictions"])


@app.get("/")
def root():
    """
    Root endpoint to verify the API is running.
    
    Returns:
        Dictionary with API information
    """
    return {
        "message": "AI Model Monitoring API is running",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health",
        "predict": "/predict",
    }
