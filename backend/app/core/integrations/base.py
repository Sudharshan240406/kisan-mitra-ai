from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class IntegrationMetadata(BaseModel):
    """
    Structured model holding standard integration adapter details.
    """
    id: str = Field(..., description="Unique provider key.")
    name: str = Field(..., description="Human-friendly name.")
    version: str = Field(..., description="Semantic version string.")
    description: str = Field(..., description="Summary details.")
    type: str = Field(..., description="Logical domain classification.")
    status: str = Field("active", description="Operational status: active, inactive, degraded.")
    capabilities: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)
    feature_flags: dict[str, bool] = Field(default_factory=dict)


class IIntegration(ABC):
    """
    Common lifecycle interface contract for all external integration adapters.
    """
    @property
    @abstractmethod
    def metadata(self) -> IntegrationMetadata:
        pass

    @abstractmethod
    async def initialize(self) -> None:
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    def get_status(self) -> str:
        return self.metadata.status

    def get_metrics(self) -> dict[str, Any]:
        return {}


class IWeatherAdapter(IIntegration, ABC):
    """
    Domain interface contract for meteorological integrations.
    """
    @abstractmethod
    async def get_forecast(self, location: str) -> dict[str, Any]:
        pass


class IMarketAdapter(IIntegration, ABC):
    """
    Domain interface contract for mandi crop pricing integrations.
    """
    @abstractmethod
    async def get_market_price(self, crop: str, location: str) -> dict[str, Any]:
        pass


class IGovernmentSchemeAdapter(IIntegration, ABC):
    """
    Domain interface contract for government schemes integrations.
    """
    @abstractmethod
    async def list_schemes(self) -> list[dict[str, Any]]:
        pass


class IStorageAdapter(IIntegration, ABC):
    """
    Domain interface contract for database, cache, or vector index operations.
    """
    @abstractmethod
    async def read(self, key: str) -> Any:
        pass

    @abstractmethod
    async def write(self, key: str, val: Any) -> None:
        pass


class INotificationAdapter(IIntegration, ABC):
    """
    Domain interface contract for SMS, email, and push alerts dispatch.
    """
    @abstractmethod
    async def send_notification(self, recipient: str, message: str) -> bool:
        pass


class IAuthenticationAdapter(IIntegration, ABC):
    """
    Domain interface contract for identity authentication.
    """
    @abstractmethod
    async def authenticate(self, username: str, token: str) -> bool:
        pass
