import logging
from typing import Any, List, Optional

from app.sms.provider_base import BaseSMSProvider

logger = logging.getLogger("kisan_mitra_ai.sms.provider_registry")


class ProviderRegistry:
    """Registry supervising loading, versioning, health, and tracking of SMS providers."""

    def __init__(self, event_bus: Optional[Any] = None, governance_engine: Optional[Any] = None) -> None:
        self._providers: dict[str, BaseSMSProvider] = {}
        self._event_bus = event_bus
        self._governance_engine = governance_engine
        self._active: str = ""

    def register(self, provider: BaseSMSProvider) -> None:
        """Registers an SMS provider into the registry."""
        name = provider.id
        self._providers[name] = provider
        if not self._active:
            self._active = name
        logger.info(f"Registered SMS Provider '{name}' v{provider.version}.")

        # Auto-register with Governance Engine if present
        if self._governance_engine:
            try:
                self._governance_engine.register_artifact(
                    artifact_type="sms_provider",
                    artifact_id=name,
                    version=provider.version,
                    status=provider.status.value
                )
            except Exception as e:
                logger.error(f"Failed to register provider '{name}' in governance ledger: {e}")

    def deregister(self, provider_id: str) -> None:
        """Deregisters an SMS provider."""
        if provider_id in self._providers:
            del self._providers[provider_id]
            logger.info(f"Deregistered SMS Provider '{provider_id}'.")

    def discover(self, provider_id: str) -> Optional[BaseSMSProvider]:
        """Looks up an SMS provider by ID."""
        return self._providers.get(provider_id)

    def list_providers(self) -> List[BaseSMSProvider]:
        """Lists all registered SMS providers."""
        return list(self._providers.values())

    def validate_dependencies(self, provider_id: str) -> bool:
        """Validates that an SMS provider is registered."""
        return provider_id in self._providers

    def set_active(self, name: str) -> None:
        if name not in self._providers:
            raise KeyError(f"SMS provider '{name}' is not registered.")
        self._active = name

    def get_active(self) -> Optional[BaseSMSProvider]:
        if not self._active:
            return None
        return self._providers.get(self._active)

    def load_from_config(self, configs: List[dict[str, Any]]) -> None:
        """Dynamically instantiates and registers mock providers from configuration."""
        from app.sms.exotel_provider import ExotelProvider
        from app.sms.fallback_provider import FallbackProvider
        from app.sms.msg91_provider import MSG91Provider
        from app.sms.twilio_provider import TwilioProvider
        for cfg in configs:
            try:
                pid = cfg.get("provider_id")
                ptype = cfg.get("provider_type")
                version = cfg.get("version", "1.0.0")
                caps = cfg.get("capabilities", [])

                if not pid or not ptype:
                    continue

                provider: BaseSMSProvider

                if ptype == "twilio":
                    provider = TwilioProvider(pid, version, caps)
                elif ptype == "exotel":
                    provider = ExotelProvider(pid, version, caps)
                elif ptype == "msg91":
                    provider = MSG91Provider(pid, version, caps)
                else:
                    provider = FallbackProvider(pid, version, caps)

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
