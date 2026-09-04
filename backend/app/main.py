from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.app.routes import (
    ai_router,
    chat_router,
    health_router,
    satellite_router,
    storms_router,
)
from backend.app.services import siglip_manager
from backend.app.utils.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application Lifespan Event Handler."""
    logger.info("Initializing StormSense FastAPI Backend...")
    # Load SigLIP model ONCE at startup (if enabled)
    siglip_manager.load_model()
    yield
    logger.info("Shutting down StormSense FastAPI Backend...")


app = FastAPI(
    title="StormSense — Live Cyclone Intelligence API",
    description=(
        "AI/ML system for identification, classification, and prediction of "
        "tropical cyclone patterns using multi-source satellite data (Ministry of Earth Sciences / IMD)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware for MapLibre & React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health_router)
app.include_router(storms_router)
app.include_router(satellite_router)
app.include_router(ai_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
