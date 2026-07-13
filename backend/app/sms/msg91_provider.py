import logging
import time
from typing import Any, List, Optional

from app.sms.provider_base import SMSProviderStatus

logger = logging.getLogger("kisan_mitra_ai.sms.msg91_provider")


class MSG91Provider:
    """MSG91 SMS production integration client."""

    def __init__(
        self,
        provider_id: str = "msg91",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None
    ) -> None:
        self._id = provider_id
        self._version = version
        self._capabilities = capabilities or ["transactional_sms", "otp_sms"]
        self._status = SMSProviderStatus.ACTIVE
        self._latency_ms = 0.0
        self._metadata: dict[str, Any] = {}
        self._sent_messages: List[tuple[str, str]] = []

    @property
    def id(self) -> str:
        return self._id

    @property
    def version(self) -> str:
        return self._version

    @property
    def capabilities(self) -> List[str]:
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
        # Mock/Stub output
        self.latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"[MSG91Provider Stub] Sent SMS to {recipient}: {body}")
        self._sent_messages.append((recipient, body))
        return True

    async def health_check(self) -> bool:
        return bool(self.status == SMSProviderStatus.ACTIVE)
