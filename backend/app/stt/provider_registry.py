import logging
from typing import Dict, List, Optional

from app.stt.provider_base import BaseSTTProvider

logger = logging.getLogger("kisan_mitra_ai.stt.provider_registry")


class ProviderRegistry:
    """Thread-safe registry managing Speech-to-Text providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, BaseSTTProvider] = {}
        self._active: str = ""

    def register(self, provider: BaseSTTProvider) -> None:
        name = provider.provider_name
        self._providers[name] = provider
        if not self._active:
            self._active = name
        logger.info(f"[STTProviderRegistry] Registered provider: '{name}'")

    def get(self, name: str) -> Optional[BaseSTTProvider]:
        return self._providers.get(name)

    def set_active(self, name: str) -> None:
        if name not in self._providers:
            raise KeyError(f"STT provider '{name}' is not registered.")
        self._active = name
        logger.info(f"[STTProviderRegistry] Set active provider to: '{name}'")

    def get_active(self) -> Optional[BaseSTTProvider]:
        if not self._active:
            return None
        return self._providers.get(self._active)

    def list_providers(self) -> List[str]:
        return list(self._providers.keys())
