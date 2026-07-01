import logging
from typing import Any, Optional

from app.core.container import Container
from app.dependencies.container import get_container
from fastapi import APIRouter, Depends, File, Form, UploadFile

router = APIRouter(prefix="/api/v1/telephony", tags=["Telephony & IVR"])
logger = logging.getLogger("kisan_mitra_ai.api.telephony")


@router.post("/inbound", response_model=dict[str, Any])
async def handle_inbound_call(
    caller: str = Form(..., description="Phone number or SIP URI of the caller"),
    callee: str = Form(..., description="Target phone number or SIP URI"),
    call_id: Optional[str] = Form(None, description="Optional incoming call identifier"),
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Handle an inbound telephony call, initiate session, and return the greeting TTS.
    """
    logger.info(f"Incoming call alert from '{caller}' to '{callee}'")
    result = await container.call_manager.handle_incoming_call(caller, callee, call_id)
    return result


@router.post("/dtmf", response_model=dict[str, Any])
async def handle_dtmf_digit(
    call_id: str = Form(..., description="Active call session identifier"),
    digits: str = Form(..., description="DTMF digits pressed by the caller"),
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Receive and process a DTMF keypress update from the telephone stream.
    """
    logger.info(f"Received DTMF '{digits}' on call '{call_id}'")
    result = await container.call_manager.handle_dtmf_input(call_id, digits)
    return result


@router.post("/voice", response_model=dict[str, Any])
async def handle_voice_voicemail(
    call_id: str = Form(..., description="Active call session identifier"),
    file: UploadFile = File(..., description="Voicemail/recorded audio payload file"),
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Ingest a voicemail audio clip, transcribe it, evaluate policies, and generate TTS advice.
    """
    logger.info(f"Ingesting voicemail recording '{file.filename}' for call '{call_id}'")
    content_bytes = await file.read()
    result = await container.call_manager.handle_voice_recording(
        call_id=call_id,
        audio_bytes=content_bytes,
        filename=file.filename or "voicemail.wav"
    )
    return result


@router.get("/providers", response_model=list[dict[str, Any]])
async def list_telephony_providers(
    container: Container = Depends(get_container)
) -> list[dict[str, Any]]:
    """
    List registered telephony adapters and their operational stats.
    """
    providers = container.telephony_provider_registry.list_providers()
    return [
        {
            "id": p.id,
            "version": p.version,
            "capabilities": p.capabilities,
            "status": p.status.value,
            "latency_ms": p.latency_ms,
            "metadata": p.metadata
        }
        for p in providers
    ]


@router.get("/calls", response_model=list[dict[str, Any]])
async def list_active_calls(
    container: Container = Depends(get_container)
) -> list[dict[str, Any]]:
    """
    List active call session logs.
    """
    sessions = container.call_session_manager.list_sessions()
    return [s.model_dump() for s in sessions]
