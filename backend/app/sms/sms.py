import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

from app.utils.id import generate_uuid
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.sms")


class SMSStatus(str, Enum):
    """SMS delivery status codes."""
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RECEIVED = "received"


class SMSProviderStatus(str, Enum):
    """Operational status of SMS provider adapters."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


class SMSMetadata(BaseModel):
    """
    Metadata describing an SMS transmission transaction.
    """
    sender: str = Field(..., description="Sender identification phone number.")
    receiver: str = Field(..., description="Recipient identification phone number.")
    body: str = Field(..., description="SMS message text body content.")
    timestamp: float = Field(default_factory=time.time, description="Creation epoch timestamp.")
    delivery_status: SMSStatus = Field(default=SMSStatus.QUEUED, description="Delivery status of the transmission.")
    retry_count: int = Field(default=0, description="Count of retry attempts.")
    custom_metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible metadata values.")


class SMSMessage(BaseModel):
    """
    Universal object representing a single SMS message.
    """
    sms_id: str = Field(default_factory=generate_uuid, description="Unique SMS identifier.")
    metadata: SMSMetadata = Field(..., description="Associated SMS parameters.")


class ISMSProvider(ABC):
    """
    Abstract interface defining capabilities that all SMS providers must implement.
    """
    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @property
    @abstractmethod
    def capabilities(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def status(self) -> SMSProviderStatus:
        pass

    @property
    @abstractmethod
    def latency_ms(self) -> float:
        pass

    @property
    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        pass

    @abstractmethod
    async def send_sms(self, recipient: str, body: str) -> bool:
        """Sends an SMS message to a recipient, returning success flag."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Checks provider health."""
        pass


class BaseSMSProvider(ISMSProvider):
    """
    Base class implementing shared attributes and boilerplate code for SMS providers.
    """
    def __init__(
        self,
        provider_id: str,
        version: str = "1.0.0",
        capabilities: Optional[list[str]] = None
    ) -> None:
        self._id = provider_id
        self._version = version
        self._capabilities = capabilities or []
        self._status = SMSProviderStatus.ACTIVE
        self._latency_ms = 0.0
        self._metadata: dict[str, Any] = {}
        self._sent_messages: list[tuple[str, str]] = []

    @property
    def id(self) -> str:
        return self._id

    @property
    def version(self) -> str:
        return self._version

    @property
    def capabilities(self) -> list[str]:
        return self._capabilities

    @property
    def status(self) -> SMSProviderStatus:
        return self._status

    @status.setter
    def status(self, val: SMSProviderStatus) -> None:
        self._status = val

    @property
    def latency_ms(self) -> float:
        return self._latency_ms

    @latency_ms.setter
    def latency_ms(self, val: float) -> None:
        self._latency_ms = val

    @property
    def metadata(self) -> dict[str, Any]:
        return self._metadata

    async def send_sms(self, recipient: str, body: str) -> bool:
        start_time = time.perf_counter()
        self._sent_messages.append((recipient, body))
        self.latency_ms = round((time.perf_counter() - start_time) * 1000, 4)
        logger.info(f"[{self.id}] Sent SMS to {recipient}: {body}")
        return True

    async def health_check(self) -> bool:
        return self._status == SMSProviderStatus.ACTIVE


class TwilioSMSProvider(BaseSMSProvider):
    """Twilio SMS adapter simulation."""
    pass


class ExotelSMSProvider(BaseSMSProvider):
    """Exotel SMS adapter simulation."""
    pass


class MSG91SMSProvider(BaseSMSProvider):
    """MSG91 SMS adapter simulation."""
    pass


class AWSSNSSMSProvider(BaseSMSProvider):
    """AWS SNS SMS adapter simulation."""
    pass


class BSNLSMSProvider(BaseSMSProvider):
    """BSNL SMS gateway adapter simulation."""
    pass


class GovSMSProvider(BaseSMSProvider):
    """Government dynamic SMS gateway adapter simulation."""
    pass


class SMSProviderRegistry:
    """
    Registry supervising loading, versioning, health, and registry tracking of SMS providers.
    """
    def __init__(self, event_bus: Optional[Any] = None, governance_engine: Optional[Any] = None) -> None:
        self._providers: dict[str, ISMSProvider] = {}
        self._event_bus = event_bus
        self._governance_engine = governance_engine

    def register(self, provider: ISMSProvider) -> None:
        """Registers an SMS provider into the registry."""
        self._providers[provider.id] = provider
        logger.info(f"Registered SMS Provider '{provider.id}' v{provider.version}.")

        # Auto-register with Governance Engine if present
        if self._governance_engine:
            try:
                self._governance_engine.register_artifact(
                    artifact_type="sms_provider",
                    artifact_id=provider.id,
                    version=provider.version,
                    status=provider.status.value
                )
            except Exception as e:
                logger.error(f"Failed to register provider '{provider.id}' in governance ledger: {e}")

    def deregister(self, provider_id: str) -> None:
        """Deregisters an SMS provider."""
        if provider_id in self._providers:
            del self._providers[provider_id]
            logger.info(f"Deregistered SMS Provider '{provider_id}'.")

    def discover(self, provider_id: str) -> Optional[ISMSProvider]:
        """Looks up an SMS provider by ID."""
        return self._providers.get(provider_id)

    def list_providers(self) -> list[ISMSProvider]:
        """Lists all registered SMS providers."""
        return list(self._providers.values())

    def validate_dependencies(self, provider_id: str) -> bool:
        """Validates that an SMS provider has its configured properties."""
        provider = self.discover(provider_id)
        if not provider:
            return False
        if not provider.id or not provider.version or not provider.status:
            return False
        return True

    def load_from_config(self, configs: list[dict[str, Any]]) -> None:
        """Dynamically instantiates and registers mock providers from a configuration array."""
        for cfg in configs:
            try:
                pid = cfg.get("provider_id")
                ptype = cfg.get("provider_type")
                version = cfg.get("version", "1.0.0")
                caps = cfg.get("capabilities", [])

                if not pid or not ptype:
                    continue

                provider: ISMSProvider

                if ptype == "twilio":
                    provider = TwilioSMSProvider(pid, version, caps)
                elif ptype == "exotel":
                    provider = ExotelSMSProvider(pid, version, caps)
                elif ptype == "msg91":
                    provider = MSG91SMSProvider(pid, version, caps)
                elif ptype == "aws_sns":
                    provider = AWSSNSSMSProvider(pid, version, caps)
                elif ptype == "bsnl":
                    provider = BSNLSMSProvider(pid, version, caps)
                elif ptype == "gov":
                    provider = GovSMSProvider(pid, version, caps)
                else:
                    provider = BaseSMSProvider(pid, version, caps)

                self.register(provider)
            except Exception as e:
                logger.error(f"Failed to load SMS provider from configuration {cfg}: {e}")

    async def health_check(self) -> dict[str, Any]:
        """Queries health check across all registered providers."""
        report: dict[str, Any] = {}
        for pid, provider in self._providers.items():
            try:
                is_healthy = await provider.health_check()
                report[pid] = {
                    "version": provider.version,
                    "status": provider.status.value,
                    "healthy": is_healthy,
                    "latency_ms": provider.latency_ms
                }
            except Exception as e:
                report[pid] = {"healthy": False, "error": str(e)}
        return report
