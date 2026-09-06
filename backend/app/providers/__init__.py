import os
from typing import Optional
from backend.app.providers.base import BaseStormProvider
from backend.app.providers.mock import MockProvider
from backend.app.providers.imd import IMDProvider
from backend.app.providers.mosdac import MOSDACProvider
from backend.app.providers.noaa import NOAAProvider

def get_provider(provider_name: Optional[str] = None) -> BaseStormProvider:
    """Factory function returning configured provider instance."""
    name = (provider_name or os.getenv("DATA_PROVIDER", "mock")).lower().strip()
    if name == "imd":
        base_url = os.getenv("IMD_BASE_URL", "https://api.imd.gov.in")
        return IMDProvider(base_url=base_url)
    elif name == "mosdac":
        base_url = os.getenv("MOSDAC_BASE_URL", "https://mosdac.gov.in/api")
        return MOSDACProvider(base_url=base_url)
    elif name == "noaa":
        base_url = os.getenv(
            "NOAA_BASE_URL",
            "https://www.ncei.noaa.gov/data/hurricane-satellite-hursat-b1/archive/v06",
        )
        return NOAAProvider(base_url=base_url)
    else:
        return MockProvider()

__all__ = [
    "BaseStormProvider",
    "MockProvider",
    "IMDProvider",
    "MOSDACProvider",
    "NOAAProvider",
    "get_provider",
]
