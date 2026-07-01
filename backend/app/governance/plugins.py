import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.governance.plugins")


class PluginMetadata(BaseModel):
    """
    Metadata representation detailing plugin metadata, versions, and capabilities.
    """
    plugin_id: str = Field(..., description="Unique plugin identifier.")
    name: str = Field(..., description="Human-readable plugin name.")
    version: str = Field(..., description="Semantic version string of the plugin.")
    description: str = Field(..., description="Plugin functionality summary details.")
    capabilities: list[str] = Field(default_factory=list, description="Capabilities introduced by this plugin.")
    agents: list[str] = Field(default_factory=list, description="Worker agents introduced by this plugin.")
    services: list[str] = Field(default_factory=list, description="Domain services introduced by this plugin.")
    tools: list[str] = Field(default_factory=list, description="Interface tools introduced by this plugin.")
    dependencies: list[str] = Field(default_factory=list, description="Required plugins/libraries checklist.")
    status: str = Field(default="active", description="Plugin state ('active', 'inactive', 'degraded').")


class IPlugin(ABC):
    """
    Standard interface contract that all third-party plugins must implement.
    """
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
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


class PluginRegistry:
    """
    Platform plugin registry supporting hot registration and discovery.
    """
    def __init__(self) -> None:
        self._plugins: dict[str, IPlugin] = {}

    def register(self, plugin: IPlugin) -> None:
        """
        Hot registers a new plugin. Throws error if ID conflicts exist.
        """
        meta = plugin.metadata
        if meta.plugin_id in self._plugins:
            existing = self._plugins[meta.plugin_id].metadata
            if existing.version == meta.version:
                logger.warning(f"Plugin '{meta.plugin_id}' version {meta.version} already registered. Overwriting.")
            else:
                raise ValueError(
                    f"Version conflict for plugin '{meta.plugin_id}': "
                    f"Cannot overwrite version {existing.version} with {meta.version} without explicit deregistration."
                )

        # Basic dependency check (simulated checklist)
        for dep in meta.dependencies:
            if dep not in self._plugins:
                logger.warning(f"Plugin '{meta.plugin_id}' requires missing dependency '{dep}'.")

        self._plugins[meta.plugin_id] = plugin
        logger.info(f"Registered plugin '{meta.plugin_id}' v{meta.version}.")

    def deregister(self, plugin_id: str) -> None:
        """
        Safely removes a plugin from active registry.
        """
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            logger.info(f"Deregistered plugin '{plugin_id}'.")

    def discover(self, plugin_id: str) -> Optional[IPlugin]:
        """
        Retrieves a registered plugin by ID.
        """
        return self._plugins.get(plugin_id)

    def list_plugins(self) -> list[IPlugin]:
        """
        Returns all registered plugins.
        """
        return list(self._plugins.values())

    async def health_check(self) -> dict[str, Any]:
        """
        Queries all plugins and reports overall platform plug-in health.
        """
        report: dict[str, Any] = {}
        for pid, plugin in self._plugins.items():
            try:
                is_healthy = await plugin.health_check()
                report[pid] = {
                    "name": plugin.metadata.name,
                    "version": plugin.metadata.version,
                    "healthy": is_healthy,
                    "status": plugin.metadata.status
                }
            except Exception as e:
                report[pid] = {
                    "name": plugin.metadata.name,
                    "version": plugin.metadata.version,
                    "healthy": False,
                    "status": "degraded",
                    "error": str(e)
                }
        return report
