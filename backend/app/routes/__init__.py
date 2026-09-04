from backend.app.routes.health import router as health_router
from backend.app.routes.storms import router as storms_router
from backend.app.routes.satellite import router as satellite_router
from backend.app.routes.ai import router as ai_router
from backend.app.routes.chat import router as chat_router

__all__ = [
    "health_router",
    "storms_router",
    "satellite_router",
    "ai_router",
    "chat_router",
]
