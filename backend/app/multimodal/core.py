from __future__ import annotations

import logging
import time
from typing import Any, Optional

from app.media.media import MediaInput, MediaType
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.multimodal.core")


class MediaContext(BaseModel):
    """Shared context propagated through multimodal processing."""

    conversation_id: str = Field(..., description="Conversation reference for this media exchange.")
    trace_id: str = Field(..., description="Trace identifier for observability.")
    media_type: MediaType = Field(..., description="Ingested media type.")
    filename: str = Field(..., description="Original filename.")
    language: str = Field(default="hi", description="Preferred farmer language.")
    crop: Optional[str] = Field(default=None, description="Resolved crop context.")
    location: Optional[str] = Field(default=None, description="Resolved location context.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional multimodal context.")


class MediaSessionRecord(BaseModel):
    """Lifecycle view of a multimodal interaction."""

    session_id: str = Field(..., description="Unique session identifier.")
    started_at: float = Field(default_factory=time.time)
    media_type: MediaType = Field(..., description="Processed media type.")
    provider_id: str = Field(..., description="Provider used for extraction.")
    reasoning_ref: Optional[str] = Field(default=None, description="Reasoning graph or result reference.")
    status: str = Field(default="running", description="running | completed | failed")
    confidence: float = Field(default=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VoiceManager:
    """Thin facade over the existing voice stack."""

    def __init__(self, stt_registry: Any, tts_registry: Any) -> None:
        self.stt_registry = stt_registry
        self.tts_registry = tts_registry

    def health(self) -> dict[str, Any]:
        return {
            "stt_providers": self.stt_registry.list_providers(),
            "tts_providers": self.tts_registry.list_providers(),
            "status": "healthy",
        }


class VisionManager:
    """Thin facade over the existing media provider registry."""

    def __init__(self, media_registry: Any) -> None:
        self.media_registry = media_registry

    def health(self) -> dict[str, Any]:
        return {
            "registered_providers": [provider.id for provider in self.media_registry.list_providers()],
            "status": "healthy",
        }


class MultimodalPlatform:
    """Top-level multimodal platform entry point."""

    def __init__(self, voice_manager: VoiceManager, vision_manager: VisionManager) -> None:
        self.voice_manager = voice_manager
        self.vision_manager = vision_manager
        self._sessions: dict[str, MediaSessionRecord] = {}
        logger.info("[MultimodalPlatform] Initialized multimodal platform.")

    def start_session(self, session_id: str, media_type: MediaType, provider_id: str) -> MediaSessionRecord:
        session = MediaSessionRecord(
            session_id=session_id,
            media_type=media_type,
            provider_id=provider_id,
        )
        self._sessions[session_id] = session
        return session

    def complete_session(
        self,
        session_id: str,
        confidence: float,
        reasoning_ref: Optional[str],
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        session = self._sessions.get(session_id)
        if not session:
            return
        session.status = "completed"
        session.confidence = confidence
        session.reasoning_ref = reasoning_ref
        if metadata:
            session.metadata.update(metadata)

    def fail_session(self, session_id: str, reason: str) -> None:
        session = self._sessions.get(session_id)
        if not session:
            return
        session.status = "failed"
        session.metadata["failure_reason"] = reason

    def build_context(
        self,
        media_input: MediaInput,
        conversation_id: str,
        trace_id: str,
        language: str = "hi",
    ) -> MediaContext:
        return MediaContext(
            conversation_id=conversation_id,
            trace_id=trace_id,
            media_type=media_input.media_type,
            filename=media_input.filename,
            language=language,
            metadata=media_input.metadata.additional_metadata,
        )

    def health(self) -> dict[str, Any]:
        active = [session for session in self._sessions.values() if session.status == "running"]
        return {
            "status": "healthy",
            "active_sessions": len(active),
            "voice_manager": self.voice_manager.health(),
            "vision_manager": self.vision_manager.health(),
        }
