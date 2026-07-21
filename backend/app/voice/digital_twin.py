"""
Kisan Mitra AI — Voice Digital Twin Integrator
================================================
Writes every completed voice call to the Digital Twin Memory (ARM).

Updates:
  - Call transcript history
  - Recommendations given
  - Confidence scores
  - Weather/market/scheme consultation flags
  - Escalation events
  - Follow-up reminders
  - Language preference (for future calls)

This module is the bridge between the Voice Platform and the
Agricultural Reasoning Memory (ARM) — the farmer's Digital Twin.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from app.voice.session import VoiceSession

logger = logging.getLogger("kisan_mitra_ai.voice.digital_twin")


class VoiceDigitalTwinIntegrator:
    """
    Syncs completed voice sessions to the Digital Twin Memory (ARM).

    Integration points:
      1. AgriculturalReasoningMemory (app.intelligence.arm) — reasoning records
      2. MemoryService (container.memory_service) — conversation persistence
      3. Container event_bus — publishes advisory_generated events
    """

    def __init__(self, container: Any) -> None:
        self._container = container
        self._total_updates: int = 0
        self._failed_updates: int = 0

    async def sync_session(self, session: VoiceSession) -> dict[str, Any]:
        """
        Writes the completed VoiceSession to the Digital Twin Memory.
        Called on every call close (complete/drop/escalate).

        Returns a sync result dict.
        """
        if session.twin_updated:
            return {"status": "already_synced", "session_id": session.session_id}

        record = session.to_twin_record()
        synced: list[str] = []
        errors: list[str] = []

        # ── 1. Persist to MemoryService (existing intelligence layer) ─────────
        try:
            if hasattr(self._container, "memory_service"):
                await self._store_to_memory_service(session, record)
                synced.append("memory_service")
        except Exception as e:
            errors.append(f"memory_service: {e}")
            logger.warning(f"[DigitalTwin] MemoryService sync failed: {e}")

        # ── 2. Save reasoning record to ARM ───────────────────────────────────
        try:
            if hasattr(self._container, "arm") and session.recommendations_given:
                await self._save_arm_record(session)
                synced.append("arm")
        except Exception as e:
            errors.append(f"arm: {e}")
            logger.warning(f"[DigitalTwin] ARM sync failed: {e}")

        # ── 3. Publish advisory_generated event ───────────────────────────────
        try:
            if hasattr(self._container, "event_bus") and session.recommendations_given:
                self._publish_advisory_event(session)
                synced.append("event_bus")
        except Exception as e:
            errors.append(f"event_bus: {e}")

        session.twin_updated = True
        self._total_updates += 1

        if errors:
            self._failed_updates += 1

        logger.info(
            f"[DigitalTwin] Synced session '{session.session_id}' → {synced}"
            + (f" | Errors: {errors}" if errors else "")
        )

        return {
            "status": "synced" if not errors else "partial",
            "session_id": session.session_id,
            "synced_to": synced,
            "errors": errors,
            "record_id": record.get("call_id"),
        }

    async def _store_to_memory_service(self, session: VoiceSession, record: dict[str, Any]) -> None:
        """Store voice call summary in MemoryService for conversation continuity."""
        memory_svc = self._container.memory_service
        # Build a conversation memory entry compatible with existing MemoryService
        entry = {
            "type": "voice_call",
            "call_id": session.call_id,
            "session_id": session.session_id,
            "language": session.detected_language,
            "duration_s": session.duration_seconds,
            "recommendations": session.recommendations_given,
            "weather_consulted": session.weather_consulted,
            "market_consulted": session.market_consulted,
            "schemes": session.schemes_discussed,
            "escalated": session.escalated,
            "transcript_turns": session.turn_count,
            "timestamp": time.time(),
            "farmer_id": session.farmer_profile.farmer_id,
        }
        # Use store method if available, else log (testing-safe)
        if hasattr(memory_svc, "store"):
            await memory_svc.store(
                session_id=session.session_id,
                key=f"voice_call_{session.call_id}",
                value=entry,
            )
        elif hasattr(memory_svc, "save"):
            memory_svc.save(session.session_id, entry)

    async def _save_arm_record(self, session: VoiceSession) -> None:
        """Save reasoning decision to Agricultural Reasoning Memory."""
        from app.intelligence.arm import (
            AgriculturalReasoningMemory,
            ReasoningMemoryRecord,
        )

        arm: AgriculturalReasoningMemory = self._container.arm
        record = ReasoningMemoryRecord(
            decision_id=f"VOICE-{uuid.uuid4().hex[:8].upper()}",
            evidence_used=[{"source": "voice", "turns": session.turn_count}],
            reasoning_path=[f"voice_call:{session.call_id}"],
            reasoning_graph={"call_id": session.call_id, "language": session.detected_language},
            decision_strategy="voice_pipeline",
            confidence=session.avg_reasoning_confidence,
            risk=0.2 if not session.escalated else 0.8,
            trace_id=session.trace_id,
            outcome=session.recommendations_given[0] if session.recommendations_given else "",
            supporting_agents=["voice_reasoning_pipeline"],
        )
        arm.save_record(record)

    def _publish_advisory_event(self, session: VoiceSession) -> None:
        """Publish advisory_generated event to event bus."""
        from app.core.event_bus import Event

        event = Event(
            event_type="voice_advisory_generated",
            trace_id=session.trace_id,
            request_id=session.call_id,
            session_id=session.session_id,
            payload={
                "call_id": session.call_id,
                "farmer_id": session.farmer_profile.farmer_id,
                "language": session.detected_language,
                "recommendations_count": len(session.recommendations_given),
                "escalated": session.escalated,
                "confidence": session.avg_reasoning_confidence,
            },
        )
        self._container.event_bus.publish(event)

    def stats(self) -> dict[str, Any]:
        return {
            "total_updates": self._total_updates,
            "failed_updates": self._failed_updates,
            "success_rate": (
                round((self._total_updates - self._failed_updates) / self._total_updates, 4)
                if self._total_updates > 0 else 1.0
            ),
        }
