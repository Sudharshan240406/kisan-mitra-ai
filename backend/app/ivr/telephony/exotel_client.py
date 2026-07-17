"""
exotel_client.py — Thin Exotel REST API client.

Reads credentials from environment via settings.
Provides helpers to build ExoML responses that the Exotel gateway plays
back to the caller, and to make outbound REST calls to Exotel's API.
"""
import logging
from typing import Optional

import httpx
from app.core.config import settings

logger = logging.getLogger("kisan_mitra_ai.ivr.telephony.exotel_client")

# ---------------------------------------------------------------------------
# ExoML helpers
# ---------------------------------------------------------------------------

_EXOML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>'


def _play_text(text: str) -> str:
    """Wrap a text string in an ExoML <Say> element, using SSML if Hindi is detected."""
    # Exotel's ExoML uses <Say> for TTS
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Detect Devanagari (Hindi) characters in the Unicode range U+0900 to U+097F
    has_hindi = any(0x0900 <= ord(char) <= 0x097F for char in text)
    if has_hindi:
        return f'<Say><speak><voice language="hi-IN">{safe}</voice></speak></Say>'
    return f"<Say>{safe}</Say>"


def _gather_with_prompt(prompt: str, action_url: str, num_digits: int = 1) -> str:
    """Return an ExoML <Gather> stanza with a nested <Say> prompt to enable barge-in."""
    say_block = _play_text(prompt) if prompt else ""
    return (
        f'<Gather action="{action_url}" method="POST" numDigits="{num_digits}" '
        f'timeout="10" finishOnKey="#">'
        f"{say_block}"
        "</Gather>"
    )


def _hangup() -> str:
    return "<Hangup/>"


# ---------------------------------------------------------------------------
# ExotelClient
# ---------------------------------------------------------------------------


class ExotelClient:
    """
    Thin wrapper around the Exotel REST API.

    Credentials are read from:
        settings.EXOTEL_SID   — Exotel account SID
        settings.EXOTEL_TOKEN — Exotel API token
        settings.EXOTEL_PHONE — Virtual phone number (ExoPhone)
    """

    def __init__(self) -> None:
        self._sid: str = settings.EXOTEL_SID
        self._token: str = settings.EXOTEL_TOKEN
        self._phone: str = settings.EXOTEL_PHONE
        self._base = f"https://api.exotel.com/v1/Accounts/{self._sid}"

    # ------------------------------------------------------------------
    # ExoML builders (returned to Exotel as webhook responses)
    # ------------------------------------------------------------------

    def build_greeting_exoml(self, prompt: str, dtmf_url: str) -> str:
        """
        Build the ExoML response for an inbound call greeting.
        Speaks the prompt and then gathers a single DTMF digit.
        """
        body = _gather_with_prompt(prompt, dtmf_url, num_digits=1)
        return f"{_EXOML_HEADER}<Response>{body}</Response>"

    def build_dtmf_exoml(self, prompt: str, dtmf_url: str, end_call: bool = False) -> str:
        """
        Build the ExoML response after a DTMF digit is received.
        Speaks the response and optionally hangs up or gathers the next digit.
        """
        if end_call:
            body = _play_text(prompt) + _hangup()
        else:
            body = _gather_with_prompt(prompt, dtmf_url, num_digits=1)
        return f"{_EXOML_HEADER}<Response>{body}</Response>"

    def build_voice_exoml(self, prompt: str, dtmf_url: str) -> str:
        """Build ExoML after a voice interaction — play the advisory and re-gather."""
        body = _gather_with_prompt(prompt, dtmf_url, num_digits=1)
        return f"{_EXOML_HEADER}<Response>{body}</Response>"

    def build_hangup_exoml(self, farewell: str = "Thank you for calling Kisan Mitra. Goodbye.") -> str:
        """Build a final ExoML farewell and hangup."""
        body = _play_text(farewell) + _hangup()
        return f"{_EXOML_HEADER}<Response>{body}</Response>"

    # ------------------------------------------------------------------
    # Outbound REST calls (best-effort — failures are logged, not raised)
    # ------------------------------------------------------------------

    async def initiate_call(self, to: str, from_: Optional[str] = None) -> Optional[str]:
        """
        Initiate an outbound call via the Exotel Connect API.
        Returns the Exotel call SID on success, None on failure.
        """
        caller = from_ or self._phone
        if not (self._sid and self._token):
            logger.warning("[ExotelClient] Credentials not configured — skipping outbound call.")
            return None
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(
                    f"{self._base}/Calls/connect.json",
                    auth=(self._sid, self._token),
                    data={"From": caller, "To": to, "CallerId": self._phone},
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    sid = data.get("Call", {}).get("Sid")
                    logger.info(f"[ExotelClient] Outbound call initiated, SID={sid}")
                    return str(sid) if sid is not None else None
                logger.warning(f"[ExotelClient] Outbound call HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as exc:
            logger.error(f"[ExotelClient] Outbound call failed: {exc}")
        return None

    async def health_check(self) -> bool:
        """Ping the Exotel API to verify credentials."""
        if not (self._sid and self._token):
            return False
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(
                    f"{self._base}.json",
                    auth=(self._sid, self._token),
                )
                return resp.status_code == 200
        except Exception:
            return False
