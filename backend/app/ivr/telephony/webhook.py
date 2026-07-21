"""
webhook.py — Exotel webhook router.

Exotel calls these endpoints during a live phone call.
Each handler:
  1. Parses Exotel's form-encoded POST body
  2. Delegates to the existing CallManager (no business logic here)
  3. Converts the result into ExoML via CallBridge
  4. Returns the ExoML as text/xml so Exotel can act on it

DTMF routing (reuses existing IVR flow):
  1 → Schemes
  2 → Weather
  3 → Market prices
  4 → Crop disease
  5 → Callback request
  9 → Repeat last prompt

Mission Control events are emitted inside CallManager — no extra wiring needed.
Post-call SMS is triggered inside CallManager when state reaches SUMMARY — no extra wiring needed.
"""
import asyncio
import logging
from typing import Any, Optional

import httpx
from app.core.config import settings
from app.core.container import Container
from app.dependencies.container import get_container
from app.ivr.telephony.call_bridge import CallBridge
from app.ivr.telephony.exotel_client import ExotelClient
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import Response

logger = logging.getLogger("kisan_mitra_ai.ivr.telephony.webhook")

router = APIRouter(prefix="/api/v1/exotel", tags=["Exotel IVR Demo"])

_XML_CONTENT_TYPE = "text/xml; charset=utf-8"

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _get_bridge(request: Request) -> CallBridge:
    """Build the CallBridge using the public base URL from the incoming request."""
    base_url = str(request.base_url).rstrip("/")
    client = ExotelClient()
    return CallBridge(client, base_url)


def _xml_response(xml: str) -> Response:
    return Response(content=xml, media_type=_XML_CONTENT_TYPE)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


async def _handle_inbound(
    request: Request,
    call_sid: Optional[str],
    from_: Optional[str],
    to: Optional[str],
    call_status: Optional[str],
    container: Container,
) -> Response:
    caller = from_ or "unknown"
    callee = to or settings.EXOTEL_PHONE or "kisan_mitra"
    call_id = call_sid or None

    result = await container.call_manager.handle_incoming_call(
        caller=caller,
        callee=callee,
        call_id=call_id,
    )
    bridge = _get_bridge(request)
    xml = bridge.greeting_to_exoml(result)
    return _xml_response(xml)


@router.post("/inbound")
async def exotel_inbound(
    request: Request,
    # Exotel sends PascalCase form fields — we accept both via aliases
    call_sid: Optional[str] = Form(None, alias="CallSid"),
    from_: Optional[str] = Form(None, alias="From"),
    to: Optional[str] = Form(None, alias="To"),
    call_status: Optional[str] = Form(None, alias="CallStatus"),
    container: Container = Depends(get_container),
) -> Response:
    """
    Exotel calls this endpoint when a farmer dials in (via POST).
    Creates an IVR session and returns the greeting ExoML.
    """
    return await _handle_inbound(request, call_sid, from_, to, call_status, container)


@router.get("/inbound")
async def exotel_inbound_get(
    request: Request,
    call_sid: Optional[str] = None,
    from_: Optional[str] = None,
    to: Optional[str] = None,
    call_status: Optional[str] = None,
    container: Container = Depends(get_container),
) -> Response:
    """
    Exotel calls this endpoint when a farmer dials in (via GET).
    Creates an IVR session and returns the greeting ExoML.
    """
    c_sid = call_sid or request.query_params.get("CallSid") or request.query_params.get("callsid")
    f_num = from_ or request.query_params.get("From") or request.query_params.get("from")
    t_num = to or request.query_params.get("To") or request.query_params.get("to")
    c_status = call_status or request.query_params.get("CallStatus") or request.query_params.get("callstatus")

    return await _handle_inbound(request, c_sid, f_num, t_num, c_status, container)


@router.post("/dtmf")
async def exotel_dtmf(
    request: Request,
    call_sid: Optional[str] = Form(None, alias="CallSid"),
    digits_lower: Optional[str] = Form(None, alias="digits"),
    digits_upper: Optional[str] = Form(None, alias="Digits"),  # Exotel may use either casing
    call_id: Optional[str] = None,  # Query param fallback (see _dtmf_url in call_bridge)
    container: Container = Depends(get_container),
) -> Response:
    """
    Exotel calls this endpoint when the farmer presses a DTMF key.
    Routes to the existing IVR DTMF handler and returns the response ExoML.

    DTMF map (defined in ivr_flow.py MAIN_MENU state):
        1 → Schemes
        2 → Weather
        3 → Market prices
        4 → Crop disease
        5 → Callback request
        9 → Repeat
    """
    # Resolve call ID from query param (embedded in URL by CallBridge) or form field
    if call_id is None:
        call_id = call_sid or "unknown"

    # Accept either 'digits' or 'Digits' from Exotel
    pressed = digits_lower or digits_upper or ""
    logger.info(f"[Exotel] DTMF — call_id={call_id} digits={pressed!r}")

    result = await container.call_manager.handle_dtmf_input(
        call_id=call_id,
        digits=pressed,
    )

    bridge = _get_bridge(request)
    xml = bridge.dtmf_result_to_exoml(result)
    return _xml_response(xml)


@router.post("/voice")
async def exotel_voice(
    request: Request,
    call_sid: Optional[str] = Form(None, alias="CallSid"),
    call_id: Optional[str] = None,  # Query param fallback
    recording_url: Optional[str] = Form(None, alias="RecordingUrl"),
    file: Optional[UploadFile] = File(None),
    container: Container = Depends(get_container),
) -> Response:
    """
    Exotel calls this endpoint with an audio recording from the farmer.
    Passes the audio through the STT → AI Orchestrator → TTS pipeline
    and returns the synthesized response as ExoML.
    """
    cid = call_id or call_sid or "unknown"
    logger.info(f"[Exotel] Voice recording — call_id={cid}, RecordingUrl={recording_url}")

    # Prefer an uploaded file; fall back to fetching from RecordingUrl
    audio_bytes = b""
    filename = "recording.wav"

    if file is not None:
        audio_bytes = await file.read()
        filename = file.filename or filename
    elif recording_url:
        try:
            auth = (settings.EXOTEL_SID, settings.EXOTEL_TOKEN) if settings.EXOTEL_SID else None
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(recording_url, auth=auth)
                if resp.status_code == 200:
                    audio_bytes = resp.content
        except Exception as exc:
            logger.warning(f"[Exotel] Could not fetch recording from {recording_url}: {exc}")

    result = await container.call_manager.handle_voice_recording(
        call_id=cid,
        audio_bytes=audio_bytes,
        filename=filename,
    )

    bridge = _get_bridge(request)
    xml = bridge.voice_result_to_exoml(result)
    return _xml_response(xml)


@router.post("/hangup")
async def exotel_hangup(
    request: Request,
    call_sid: Optional[str] = Form(None, alias="CallSid"),
    call_status: Optional[str] = Form(None, alias="CallStatus"),
    call_duration: Optional[str] = Form(None, alias="CallDuration"),
    container: Container = Depends(get_container),
) -> Response:
    """
    Exotel calls this endpoint when a call ends (hangup/disconnection).
    Closes the session and emits Mission Control WebSocket events.
    """
    call_id = call_sid or "unknown"
    duration = float(call_duration or 0)
    logger.info(f"[Exotel] Hangup — call_id={call_id}, status={call_status}, duration={duration}s")

    # Close the IVR session gracefully
    try:
        session_manager = container.call_session_manager
        session = session_manager.get_session(call_id)
        if session:
            from app.api.v1.websocket import ws_manager
            asyncio.ensure_future(ws_manager.push_event("CALL_COMPLETED", {
                "call_id": call_id,
                "duration": duration,
                "status": call_status or "completed",
                "summary": session.summary.model_dump() if session.summary else {},
            }))
            session_manager.close_session(call_id)
    except Exception as exc:
        logger.warning(f"[Exotel] Error during hangup cleanup for {call_id}: {exc}")

    bridge = _get_bridge(request)
    return _xml_response(bridge.hangup_exoml())


@router.get("/health")
async def exotel_health() -> dict[str, Any]:
    """Verify Exotel credentials and connectivity."""
    client = ExotelClient()
    ok = await client.health_check()
    return {
        "provider": "exotel",
        "configured": bool(settings.EXOTEL_SID and settings.EXOTEL_TOKEN),
        "reachable": ok,
        "exotel_phone": settings.EXOTEL_PHONE or "not configured",
    }
