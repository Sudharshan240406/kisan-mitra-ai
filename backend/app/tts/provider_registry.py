import logging
from typing import Dict, List, Optional

from app.tts.provider_base import BaseTTSProvider

logger = logging.getLogger("kisan_mitra_ai.tts.provider_registry")


class ProviderRegistry:
    """Thread-safe registry managing Text-to-Speech providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, BaseTTSProvider] = {}
        self._active: str = ""

    def register(self, provider: BaseTTSProvider) -> None:
        name = provider.provider_name
        self._providers[name] = provider
        if not self._active:
            self._active = name
        logger.info(f"[TTSProviderRegistry] Registered provider: '{name}'")

    def get(self, name: str) -> Optional[BaseTTSProvider]:
        return self._providers.get(name)

    def set_active(self, name: str) -> None:
        if name not in self._providers:
            raise KeyError(f"TTS provider '{name}' is not registered.")
        self._active = name
        logger.info(f"[TTSProviderRegistry] Set active provider to: '{name}'")

    def get_active(self) -> Optional[BaseTTSProvider]:
        if not self._active:
            return None
        return self._providers.get(self._active)

    def list_providers(self) -> List[str]:
        return list(self._providers.keys())
