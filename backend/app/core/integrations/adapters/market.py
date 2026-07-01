import logging
from typing import Any

from app.core.integrations.base import IMarketAdapter, IntegrationMetadata

logger = logging.getLogger("kisan_mitra_ai.integrations.adapters.market")


class AgmarknetMarketAdapter(IMarketAdapter):
    """
    Agmarknet Government Mandi Prices Integration Adapter.
    """
    def __init__(self) -> None:
        self._metadata = IntegrationMetadata(
            id="agmarknet",
            name="Agmarknet Mandi Rates",
            version="1.0.0",
            description="Agmarknet official mandi pricing service registry.",
            type="market",
            capabilities=["mandi_prices"],
            configuration={"api_endpoint": "https://agmarknet.gov.in/api"},
            feature_flags={"enabled": True}
        )

    @property
    def metadata(self) -> IntegrationMetadata:
        return self._metadata

    async def initialize(self) -> None:
        logger.info("Initializing Agmarknet Market Adapter...")

    async def cleanup(self) -> None:
        logger.info("Cleaning up Agmarknet Market Adapter resources...")

    async def health_check(self) -> bool:
        return True

    async def get_market_price(self, crop: str, location: str) -> dict[str, Any]:
        logger.info(f"Fetching Agmarknet price for crop: {crop} in location: {location}")
        return {
            "provider": "Agmarknet",
            "crop": crop,
            "location": location,
            "min_price_per_quintal": 2200,
            "max_price_per_quintal": 2450,
            "modal_price_per_quintal": 2350,
            "currency": "INR"
        }


class eNAMMarketAdapter(IMarketAdapter):
    """
    eNAM National Agriculture Market Integration Adapter.
    """
    def __init__(self) -> None:
        self._metadata = IntegrationMetadata(
            id="enam",
            name="eNAM Digital Market",
            version="1.0.0",
            description="eNAM digital platform API provider registry.",
            type="market",
            capabilities=["mandi_prices", "bidding"],
            configuration={"api_endpoint": "https://enam.gov.in/api"},
            feature_flags={"enabled": False}
        )

    @property
    def metadata(self) -> IntegrationMetadata:
        return self._metadata

    async def initialize(self) -> None:
        logger.info("Initializing eNAM Market Adapter...")

    async def cleanup(self) -> None:
        logger.info("Cleaning up eNAM Market Adapter resources...")

    async def health_check(self) -> bool:
        return True

    async def get_market_price(self, crop: str, location: str) -> dict[str, Any]:
        logger.info(f"Fetching eNAM price for crop: {crop} in location: {location}")
        return {
            "provider": "eNAM",
            "crop": crop,
            "location": location,
            "min_price_per_quintal": 2150,
            "max_price_per_quintal": 2500,
            "modal_price_per_quintal": 2300,
            "currency": "INR"
        }
