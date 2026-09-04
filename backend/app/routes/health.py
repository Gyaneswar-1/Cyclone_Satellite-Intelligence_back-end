from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/", summary="Root API Health Check")
async def root():
    """Root endpoint verifying API availability."""
    return {"status": "ok", "service": "StormSense Live Cyclone Intelligence Backend", "version": "1.0.0"}


@router.get("/health", summary="Health Status")
async def health():
    """Standard health check endpoint."""
    return {"status": "ok"}
