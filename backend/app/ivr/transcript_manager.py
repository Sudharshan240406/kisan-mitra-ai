import logging
import time
from typing import Any, Optional
from app.ivr.call_session import CallSession, TranscriptEntry

logger = logging.getLogger("kisan_mitra_ai.ivr.transcript_manager")


class TranscriptManager:
    """Tracks conversation transcripts for active voice calls and streams updates to Mission Control."""

    def add_entry(
        self,
        session: CallSession,
        sender: str,  # "farmer" or "system"
        text: str,
        confidence: float = 1.0,
        execution_id: Optional[str] = None,
        timing_ms: float = 0.0
    ) -> None:
        entry = TranscriptEntry(
            sender=sender,
            text=text,
            timestamp=time.time(),
            confidence=confidence,
            execution_id=execution_id,
            timing_ms=timing_ms
        )
        session.transcript.append(entry)
        logger.info(f"[Call {session.call_id}] Transcript entry added for {sender}: {text[:60]}")

        # Broadcast live transcript event to Mission Control WebSocket
        try:
            from app.api.v1.websocket import ws_manager
            import asyncio
            
            # Format display string for Mission Control
            full_transcript_str = "\n".join(
                f"{e.sender.capitalize()}: {e.text}" for e in session.transcript
            )
            
            event_payload = {
                "call_id": session.call_id,
                "conversation_id": session.conversation_id,
                "sender": sender,
                "text": text,
                "confidence": confidence,
                "timing_ms": timing_ms,
                "transcript": full_transcript_str,
                "timestamp": time.time(),
            }
            # Schedule push_event in the active event loop if possible
            asyncio.ensure_future(ws_manager.push_event("TRANSCRIPT_UPDATED", event_payload))
        except Exception as e:
            logger.warning(f"Could not push transcript update to Mission Control: {e}")
