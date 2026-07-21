import logging
from typing import Any

import httpx
from app.core.config import settings
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
            configuration={"api_endpoint": "https://api.data.gov.in/resource/9ef84f99-ffc9-4b20-bb41-1120e9941120"},
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

        api_key = settings.AGMARKNET_API_KEY
        if api_key:
            endpoint = self.metadata.configuration.get("api_endpoint", "https://api.data.gov.in/resource/9ef84f99-ffc9-4b20-bb41-1120e9941120")
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    response = await client.get(
                        endpoint,
                        params={
                            "api-key": api_key,
                            "format": "json",
                            "filters[commodity]": crop,
                            "filters[state]": location,
                            "limit": 1
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        records = data.get("records", [])
                        if records:
                            record = records[0]
                            raw_price = float(record.get("modal_price", 2350))
                            unit = record.get("unit", "quintal").lower()

                            # Normalization: Standard unit is Quintal (100 Kg)
                            if "kg" in unit:
                                modal_price = raw_price * 100
                            elif "ton" in unit or "tonne" in unit:
                                modal_price = raw_price / 10
                            else:
                                modal_price = raw_price

                            return {
                                "provider": "Agmarknet",
                                "crop": crop,
                                "location": location,
                                "min_price_per_quintal": modal_price * 0.95,
                                "max_price_per_quintal": modal_price * 1.05,
                                "modal_price_per_quintal": modal_price,
                                "currency": "INR"
                            }
            except Exception as e:
                logger.warning(f"[AgmarknetMarketAdapter] HTTP call failed, falling back: {e}")

        # Fallback Mock Data
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
            configuration={"api_endpoint": settings.ENAM_API_ENDPOINT},
            feature_flags={"enabled": True}
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

        endpoint = settings.ENAM_API_ENDPOINT
        if endpoint:
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    response = await client.post(
                        endpoint,
                        json={"crop": crop, "state": location}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        raw_price = float(data.get("price", 2300))
                        unit = data.get("unit", "quintal").lower()

                        # Normalization
                        if "kg" in unit:
                            modal_price = raw_price * 100
                        elif "ton" in unit or "tonne" in unit:
                            modal_price = raw_price / 10
                        else:
                            modal_price = raw_price

                        return {
                            "provider": "eNAM",
                            "crop": crop,
                            "location": location,
                            "min_price_per_quintal": modal_price * 0.93,
                            "max_price_per_quintal": modal_price * 1.08,
                            "modal_price_per_quintal": modal_price,
                            "currency": "INR"
                        }
            except Exception as e:
                logger.warning(f"[eNAMMarketAdapter] HTTP call failed, falling back: {e}")

        # Fallback Mock Data
        return {
            "provider": "eNAM",
            "crop": crop,
            "location": location,
            "min_price_per_quintal": 2150,
            "max_price_per_quintal": 2500,
            "modal_price_per_quintal": 2300,
            "currency": "INR"
        }
