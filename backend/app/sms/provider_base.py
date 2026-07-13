import logging
import time
from enum import Enum
from typing import Any, List, Protocol, runtime_checkable

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.sms.provider_base")


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
    """Metadata describing an SMS transmission transaction."""
    sender: str = Field(..., description="Sender identification phone number.")
    receiver: str = Field(..., description="Recipient identification phone number.")
    body: str = Field(..., description="SMS message text body content.")
    timestamp: float = Field(default_factory=time.time, description="Creation epoch timestamp.")
    delivery_status: SMSStatus = Field(default=SMSStatus.QUEUED, description="Delivery status of the transmission.")
    retry_count: int = Field(default=0, description="Count of retry attempts.")
    custom_metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible metadata values.")


class SMSMessage(BaseModel):
    """Universal object representing a single SMS message."""
    sms_id: str = Field(..., description="Unique SMS identifier.")
    metadata: SMSMetadata = Field(..., description="Associated SMS parameters.")


@runtime_checkable
class BaseSMSProvider(Protocol):
    """Protocol contract defining capabilities that all SMS providers must implement."""

    @property
    def id(self) -> str:
        """Unique ID of this provider."""
        ...

    @property
    def version(self) -> str:
        """Version code of this provider."""
        ...

    @property
    def capabilities(self) -> List[str]:
        ...

    @property
    def status(self) -> SMSProviderStatus:
        ...

    @property
    def latency_ms(self) -> float:
        ...

    @property
    def metadata(self) -> dict[str, Any]:
        ...

    async def send_sms(self, recipient: str, body: str) -> bool:
        """Sends an SMS message to a recipient, returning success flag."""
        ...

    async def health_check(self) -> bool:
        """Checks provider health."""
        ...
