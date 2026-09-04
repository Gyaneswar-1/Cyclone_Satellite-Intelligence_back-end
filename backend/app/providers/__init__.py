import os
from backend.app.providers.base import BaseStormProvider
from backend.app.providers.mock import MockProvider
from backend.app.providers.imd import IMDProvider
from backend.app.providers.mosdac import MOSDACProvider
from backend.app.providers.noaa import NOAAProvider

def get_provider() -> BaseStormProvider:
    """Factory function returning configured provider instance."""
    provider_name = os.getenv("DATA_PROVIDER", "mock").lower()
    if provider_name == "imd":
        base_url = os.getenv("IMD_BASE_URL", "https://api.imd.gov.in")
        return IMDProvider(base_url=base_url)
    elif provider_name == "mosdac":
        base_url = os.getenv("MOSDAC_BASE_URL", "https://mosdac.gov.in/api")
        return MOSDACProvider(base_url=base_url)
    elif provider_name == "noaa":
        base_url = os.getenv("NOAA_BASE_URL", "")
        return NOAAProvider(base_url=base_url) if base_url else NOAAProvider()
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
