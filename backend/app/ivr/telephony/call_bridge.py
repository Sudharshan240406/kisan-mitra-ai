"""
call_bridge.py — Converts CallManager dict results into Exotel ExoML responses.

Keeps the webhook thin: all business logic stays in CallManager;
this module only handles the translation layer.
"""
import logging
from typing import Any, Dict

from app.ivr.telephony.exotel_client import ExotelClient

logger = logging.getLogger("kisan_mitra_ai.ivr.telephony.call_bridge")

# States that should trigger a call hangup
_TERMINAL_STATES = {"EXIT", "HUMAN_TRANSFER"}


class CallBridge:
    """
    Translates CallManager response dicts into ExoML XML strings suitable
    for returning to the Exotel gateway as HTTP responses.
    """

    def __init__(self, exotel_client: ExotelClient, base_url: str) -> None:
        """
        Args:
            exotel_client: The ExotelClient instance.
            base_url:      Public base URL of this backend (e.g. https://api.example.com).
                           Used to construct webhook callback URLs embedded in ExoML.
        """
        self._client = exotel_client
        self._base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------

    def _dtmf_url(self, call_id: str) -> str:
        return f"{self._base_url}/api/v1/exotel/dtmf?call_id={call_id}"

    def _voice_url(self, call_id: str) -> str:
        return f"{self._base_url}/api/v1/exotel/voice?call_id={call_id}"

    # ------------------------------------------------------------------
    # Conversion methods
    # ------------------------------------------------------------------

    def greeting_to_exoml(self, call_result: Dict[str, Any]) -> str:
        """
        Convert the result of CallManager.handle_incoming_call() into ExoML.
        Plays the greeting prompt and opens a DTMF gather for the caller.
        """
        call_id = str(call_result.get("call_id", "unknown"))
        prompt = str(call_result.get("tts_prompt", "Welcome to Kisan Mitra."))
        dtmf_url = self._dtmf_url(call_id)
        logger.info(f"[CallBridge] Building greeting ExoML for call {call_id}")
        return str(self._client.build_greeting_exoml(prompt, dtmf_url))

    def dtmf_result_to_exoml(self, call_result: Dict[str, Any]) -> str:
        """
        Convert the result of CallManager.handle_dtmf_input() into ExoML.
        Plays the response; hangs up if the call has reached a terminal state.
        """
        call_id = str(call_result.get("call_id", "unknown"))
        prompt = str(call_result.get("tts_prompt", ""))
        current_state: str = str(call_result.get("current_state", ""))
        end_call = current_state in _TERMINAL_STATES

        dtmf_url = self._dtmf_url(call_id)
        logger.info(f"[CallBridge] Building DTMF ExoML for call {call_id}, state={current_state}, end={end_call}")

        if end_call:
            return str(self._client.build_hangup_exoml(farewell=prompt or "Thank you for calling Kisan Mitra. Goodbye."))
        return str(self._client.build_dtmf_exoml(prompt, dtmf_url, end_call=False))

    def voice_result_to_exoml(self, call_result: Dict[str, Any]) -> str:
        """
        Convert the result of CallManager.handle_voice_recording() into ExoML.
        Plays the AI advisory response and re-opens DTMF gather.
        """
        call_id = str(call_result.get("call_id", "unknown"))
        prompt = str(call_result.get("tts_prompt", call_result.get("advisory_text", "")))
        dtmf_url = self._dtmf_url(call_id)
        logger.info(f"[CallBridge] Building voice ExoML for call {call_id}")
        return str(self._client.build_voice_exoml(prompt, dtmf_url))

    def hangup_exoml(self) -> str:
        """Return a plain hangup ExoML."""
        return str(self._client.build_hangup_exoml())
