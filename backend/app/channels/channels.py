import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.channels")


class ChannelType(str, Enum):
    """Supported communication channel types."""
    VOICE = "voice"
    SMS = "sms"
    IVR = "ivr"
    WHATSAPP = "whatsapp"
    MOBILE_APP = "mobile_app"
    WEB_CHAT = "web_chat"


class ChannelStatus(str, Enum):
    """Channel lifecycle status codes."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


class ChannelMetadata(BaseModel):
    """
    Declarative metadata describing a communication channel.
    """
    channel_id: str = Field(..., description="Unique channel identifier.")
    channel_type: ChannelType = Field(..., description="Communication channel type.")
    name: str = Field(..., description="Human-readable channel name.")
    version: str = Field(default="1.0.0", description="Channel implementation version.")
    status: ChannelStatus = Field(default=ChannelStatus.ACTIVE, description="Current operational status.")
    capabilities: list[str] = Field(default_factory=list, description="Supported interaction capabilities.")
    supported_media: list[str] = Field(default_factory=list, description="Supported media types (text, audio, image).")
    health: str = Field(default="healthy", description="Health indicator.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible configuration metadata.")


class IChannel(ABC):
    """
    Abstract interface that all communication channels must implement.
    """
    @property
    @abstractmethod
    def channel_metadata(self) -> ChannelMetadata:
        pass

    @abstractmethod
    async def send(self, recipient: str, payload: dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def receive(self) -> Optional[dict[str, Any]]:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass


class BaseChannel(IChannel):
    """
    Base class for mock channel implementations.
    """
    def __init__(self, metadata: ChannelMetadata) -> None:
        self._metadata = metadata
        self._received_queue: list[dict[str, Any]] = []
        self._sent_messages: list[tuple[str, dict[str, Any]]] = []

    @property
    def channel_metadata(self) -> ChannelMetadata:
        return self._metadata

    async def send(self, recipient: str, payload: dict[str, Any]) -> bool:
        self._sent_messages.append((recipient, payload))
        logger.info(f"[{self._metadata.channel_id}] Sent payload to {recipient}: {payload}")
        return True

    async def receive(self) -> Optional[dict[str, Any]]:
        if self._received_queue:
            return self._received_queue.pop(0)
        return None

    async def health_check(self) -> bool:
        return self._metadata.status == ChannelStatus.ACTIVE

    def enqueue_received(self, payload: dict[str, Any]) -> None:
        """Enqueues a message simulated as received from this channel."""
        self._received_queue.append(payload)


class VoiceChannel(BaseChannel):
    """Voice communication channel."""
    pass


class SMSChannel(BaseChannel):
    """SMS text communication channel."""
    pass


class IVRChannel(BaseChannel):
    """Interactive Voice Response channel."""
    pass


class WhatsAppChannel(BaseChannel):
    """WhatsApp communication channel."""
    pass


class MobileAppChannel(BaseChannel):
    """Mobile application communication channel."""
    pass


class WebChatChannel(BaseChannel):
    """Web chat communication channel."""
    pass


class ChannelRegistry:
    """
    Registry managing communication channel registration, discovery, and health monitoring.
    """
    def __init__(self, event_bus: Optional[Any] = None) -> None:
        self._channels: dict[str, IChannel] = {}
        self._event_bus = event_bus

    def register(self, channel: IChannel) -> None:
        """Registers a communication channel."""
        meta = channel.channel_metadata
        self._channels[meta.channel_id] = channel
        logger.info(f"Registered channel '{meta.channel_id}' ({meta.channel_type.value}).")

        if self._event_bus:
            try:
                from app.channels.events import ChannelEventType
                from app.core.event_bus import Event
                self._event_bus.publish(Event(
                    event_type=ChannelEventType.CHANNEL_CONNECTED.value,
                    trace_id="system_setup",
                    request_id="system_setup",
                    session_id="system",
                    payload={"channel_id": meta.channel_id, "channel_type": meta.channel_type.value}
                ))
            except Exception as e:
                logger.error(f"Failed to publish channel connected event: {e}")

    def deregister(self, channel_id: str) -> None:
        """Removes a channel from the registry."""
        if channel_id in self._channels:
            del self._channels[channel_id]
            logger.info(f"Deregistered channel '{channel_id}'.")

            if self._event_bus:
                try:
                    from app.channels.events import ChannelEventType
                    from app.core.event_bus import Event
                    self._event_bus.publish(Event(
                        event_type=ChannelEventType.CHANNEL_DISCONNECTED.value,
                        trace_id="system_teardown",
                        request_id="system_teardown",
                        session_id="system",
                        payload={"channel_id": channel_id}
                    ))
                except Exception as e:
                    logger.error(f"Failed to publish channel disconnected event: {e}")

    def discover(self, channel_id: str) -> Optional[IChannel]:
        """Discovers a channel by ID."""
        return self._channels.get(channel_id)

    def discover_by_type(self, channel_type: ChannelType) -> list[IChannel]:
        """Discovers all channels matching a type."""
        return [
            ch for ch in self._channels.values()
            if ch.channel_metadata.channel_type == channel_type
        ]

    def discover_by_capability(self, capability: str) -> list[IChannel]:
        """Discovers all channels matching a capability."""
        return [
            ch for ch in self._channels.values()
            if capability in ch.channel_metadata.capabilities
        ]

    def get_channel_versions(self) -> dict[str, str]:
        """Returns a mapping of channel IDs to their version strings."""
        return {
            cid: ch.channel_metadata.version
            for cid, ch in self._channels.items()
        }

    def validate_dependencies(self, channel_id: str) -> bool:
        """
        Validates configurations or requirements for a specific channel.
        For example, checking if required keys exist in channel metadata.
        """
        channel = self.discover(channel_id)
        if not channel:
            logger.warning(f"Validation failed: Channel '{channel_id}' not found.")
            return False

        meta = channel.channel_metadata
        if not meta.channel_id or not meta.name or not meta.version:
            logger.warning(f"Validation failed for '{channel_id}': missing critical metadata fields.")
            return False

        if meta.channel_type == ChannelType.WHATSAPP:
            if "api_endpoint" not in meta.metadata:
                logger.warning(f"WhatsApp channel '{channel_id}' missing 'api_endpoint' configuration.")
                return False
        elif meta.channel_type == ChannelType.SMS:
            if "sms_provider" not in meta.metadata:
                logger.warning(f"SMS channel '{channel_id}' missing 'sms_provider' configuration.")
                return False

        return True

    def load_from_config(self, configs: list[dict[str, Any]]) -> None:
        """
        Dynamically loads and registers channels from a configuration list.
        Each config dict must contain at least 'channel_id', 'channel_type', and 'name'.
        """
        for config in configs:
            try:
                channel_id = config.get("channel_id")
                type_str = config.get("channel_type")
                name = config.get("name")
                if not channel_id or not type_str or not name:
                    logger.warning(f"Skipping invalid channel config: {config}")
                    continue

                channel_type = ChannelType(type_str)
                status_str = config.get("status", "active")
                status = ChannelStatus(status_str)

                metadata = ChannelMetadata(
                    channel_id=channel_id,
                    channel_type=channel_type,
                    name=name,
                    version=config.get("version", "1.0.0"),
                    status=status,
                    capabilities=config.get("capabilities", []),
                    supported_media=config.get("supported_media", []),
                    health=config.get("health", "healthy"),
                    metadata=config.get("metadata", {})
                )

                channel: IChannel
                if channel_type == ChannelType.VOICE:
                    channel = VoiceChannel(metadata)
                elif channel_type == ChannelType.SMS:
                    channel = SMSChannel(metadata)
                elif channel_type == ChannelType.IVR:
                    channel = IVRChannel(metadata)
                elif channel_type == ChannelType.WHATSAPP:
                    channel = WhatsAppChannel(metadata)
                elif channel_type == ChannelType.MOBILE_APP:
                    channel = MobileAppChannel(metadata)
                elif channel_type == ChannelType.WEB_CHAT:
                    channel = WebChatChannel(metadata)
                else:
                    channel = BaseChannel(metadata)

                self.register(channel)
            except Exception as e:
                logger.error(f"Failed to load channel from config {config}: {e}")

    def list_channels(self) -> list[IChannel]:
        """Returns all registered channels."""
        return list(self._channels.values())

    async def health_check(self) -> dict[str, Any]:
        """Queries health across all registered channels."""
        report: dict[str, Any] = {}
        for cid, channel in self._channels.items():
            try:
                is_healthy = await channel.health_check()
                meta = channel.channel_metadata
                report[cid] = {
                    "name": meta.name,
                    "type": meta.channel_type.value,
                    "version": meta.version,
                    "status": meta.status.value,
                    "healthy": is_healthy
                }
            except Exception as e:
                report[cid] = {"healthy": False, "error": str(e)}
        return report

