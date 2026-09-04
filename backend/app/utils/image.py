from io import BytesIO
from pathlib import Path
from typing import Optional
from PIL import Image
import httpx

from backend.app.utils.logging import logger

async def load_image_from_url_or_path(location: str) -> Optional[Image.Image]:
    """Load PIL Image from local file path or remote HTTP URL safely."""
    if not location:
        return None

    path = Path(location)
    if path.exists() and path.is_file():
        try:
            return Image.open(path).convert("RGB")
        except Exception as e:
            logger.warning(f"Failed to load image from local path {location}: {e}")
            return None

    if location.startswith("http://") or location.startswith("https://"):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(location)
                resp.raise_for_status()
                return Image.open(BytesIO(resp.content)).convert("RGB")
        except Exception as e:
            logger.warning(f"Failed to fetch image from URL {location}: {e}")
            return None

    return None
