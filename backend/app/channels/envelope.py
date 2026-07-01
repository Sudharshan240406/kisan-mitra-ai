import time
from enum import Enum
from typing import Any, Optional

from app.utils.id import generate_uuid
from pydantic import BaseModel, Field


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class LanguageMetadata(BaseModel):
    """
    Multi-language tracking metadata for future translation support.
    """
    preferred_language: str = Field(default="hi", description="ISO 639-1 language code.")
    locale: str = Field(default="hi-IN", description="Full locale identifier.")
    region: str = Field(default="IN", description="ISO 3166-1 region code.")
    script: str = Field(default="Devanagari", description="Script system identifier.")
    future_translation_enabled: bool = Field(default=False, description="Future translation support flag.")


class MessageEnvelope(BaseModel):
    """
    Universal message model for all channel communications.
    The Conversation Platform processes envelopes rather than channel-specific messages.
    """
    message_id: str = Field(default_factory=generate_uuid, description="Unique message identifier.")
    conversation_id: str = Field(..., description="Conversation session reference.")
    channel: str = Field(..., description="Originating channel identifier.")
    sender: str = Field(..., description="Sender identity (farmer ID, phone, user ID).")
    receiver: str = Field(default="system", description="Receiver identity.")
    language: LanguageMetadata = Field(default_factory=LanguageMetadata, description="Language context.")
    timestamp: float = Field(default_factory=time.time, description="Message creation epoch.")
    payload: dict[str, Any] = Field(default_factory=dict, description="Message content payload.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible metadata.")
    attachments: list[dict[str, Any]] = Field(default_factory=list, description="Future attachment placeholders.")
    priority: MessagePriority = Field(default=MessagePriority.NORMAL, description="Message priority level.")
    correlation_id: Optional[str] = Field(default=None, description="Correlation ID for request-response pairing.")
    trace_id: Optional[str] = Field(default=None, description="Distributed trace ID for observability.")


class ResponseEnvelope(BaseModel):
    """
    Response message routed back to the originating channel.
    """
    response_id: str = Field(default_factory=generate_uuid, description="Unique response identifier.")
    message_id: str = Field(..., description="Original message ID reference.")
    conversation_id: str = Field(..., description="Conversation session reference.")
    channel: str = Field(..., description="Target channel for response delivery.")
    receiver: str = Field(..., description="Response recipient identity.")
    language: LanguageMetadata = Field(default_factory=LanguageMetadata, description="Response language context.")
    timestamp: float = Field(default_factory=time.time, description="Response creation epoch.")
    payload: dict[str, Any] = Field(default_factory=dict, description="Response content payload.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible metadata.")
    trace_id: Optional[str] = Field(default=None, description="Distributed trace ID.")
    status: str = Field(default="success", description="Response delivery status.")
