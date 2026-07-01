import logging
from typing import Any, Optional

from app.core.event_bus import Event, EventBus
from app.core.integrations.base import IIntegration

logger = logging.getLogger("kisan_mitra_ai.integrations.registry")


class IntegrationRegistry:
    """
    Registry that coordinates runtime registration, discovery, dynamic activation state,
    and event propagation for the External Integrations Platform.
    """
    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._integrations: dict[str, IIntegration] = {}
        self.event_bus = event_bus
        self._active_providers: dict[str, str] = {}
        logger.info("IntegrationRegistry successfully initialized.")

    def register(self, integration: IIntegration) -> None:
        """
        Registers an integration provider instance.
        """
        meta = integration.metadata
        if meta.id in self._integrations:
            raise ValueError(f"Integration with ID '{meta.id}' is already registered.")

        self._integrations[meta.id] = integration

        # Set as active if it's the first of its type
        if meta.type not in self._active_providers:
            self._active_providers[meta.type] = meta.id

        logger.info(f"Registered integration '{meta.id}' of type '{meta.type}'.")

    def deregister(self, integration_id: str) -> None:
        """
        Deregisters an integration provider from the active mapping.
        """
        if integration_id in self._integrations:
            integration = self._integrations[integration_id]
            del self._integrations[integration_id]

            if self._active_providers.get(integration.metadata.type) == integration_id:
                del self._active_providers[integration.metadata.type]
                # Fallback to another provider of same type
                for other_id, other_int in self._integrations.items():
                    if other_int.metadata.type == integration.metadata.type:
                        self._active_providers[integration.metadata.type] = other_id
                        break
            logger.info(f"Deregistered integration '{integration_id}'.")

    def get(self, integration_id: str) -> IIntegration:
        """
        Retrieves registered integration by ID.
        """
        integration = self._integrations.get(integration_id)
        if not integration:
            raise KeyError(f"Integration '{integration_id}' was not found in the registry.")
        return integration

    def get_active(self, type_str: str) -> Optional[IIntegration]:
        """
        Retrieves the currently active integration instance for a domain type.
        """
        provider_id = self._active_providers.get(type_str)
        if provider_id:
            return self._integrations.get(provider_id)
        return None

    def set_active(self, type_str: str, provider_id: str) -> None:
        """
        Changes the active provider of a specific type.
        """
        if provider_id not in self._integrations:
            raise ValueError(f"Cannot select '{provider_id}' as active: Not registered.")
        integration = self._integrations[provider_id]
        if integration.metadata.type != type_str:
            raise ValueError(
                f"Cannot select '{provider_id}' as active for type '{type_str}': "
                f"Its type is '{integration.metadata.type}'."
            )
        if integration.metadata.status != "active":
            raise ValueError(
                f"Cannot select '{provider_id}' as active because its status is '{integration.metadata.status}'."
            )
        self._active_providers[type_str] = provider_id
        logger.info(f"Set active integration for type '{type_str}' to '{provider_id}'.")

    def list_integrations(self) -> list[IIntegration]:
        """
        Lists all registered integrations.
        """
        return list(self._integrations.values())

    async def run_health_checks(self) -> dict[str, Any]:
        """
        Triggers health checks for all integrations and publishes changes.
        """
        report: dict[str, Any] = {}
        for provider_id, integration in self._integrations.items():
            meta = integration.metadata
            old_status = meta.status
            try:
                is_healthy = await integration.health_check()
                new_status = "active" if is_healthy else "degraded"
            except Exception as e:
                logger.error(f"Health check failed for '{provider_id}': {e!s}")
                new_status = "offline"

            if old_status != new_status:
                meta.status = new_status
                if self.event_bus:
                    self.event_bus.publish(Event(
                        event_type="HealthChanged",
                        trace_id="system",
                        request_id="system",
                        session_id="system",
                        payload={
                            "integration_id": provider_id,
                            "old_status": old_status,
                            "new_status": new_status
                        }
                    ))

            report[provider_id] = {
                "name": meta.name,
                "type": meta.type,
                "status": new_status,
                "active": self._active_providers.get(meta.type) == provider_id
            }
        return report
