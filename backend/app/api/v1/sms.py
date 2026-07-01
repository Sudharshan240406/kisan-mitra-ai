import logging
from typing import Any, Optional

from app.core.container import Container
from app.dependencies.container import get_container
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.api.sms")

router = APIRouter(prefix="/api/v1/sms", tags=["SMS Intelligence"])


class InboundSMSRequest(BaseModel):
    sender: str = Field(..., description="Phone number of the sender.")
    body: str = Field(..., description="Text content body.")
    receiver: str = Field(default="kisan_mitra_sms")


class OutboundSMSRequest(BaseModel):
    recipient: str = Field(..., description="Recipient phone number.")
    body: str = Field(..., description="SMS reply body content.")
    provider_id: Optional[str] = Field(default=None, description="Optional provider identifier.")




@router.post("/inbound", status_code=status.HTTP_200_OK)
async def handle_inbound_sms(
    payload: InboundSMSRequest,
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Webhook receiving incoming SMS. Routes content to the multi-agent graph.
    """
    logger.info(f"Received inbound SMS webhook from {payload.sender}: {payload.body[:30]}")
    try:
        result = await container.sms_pipeline.execute(
            sender_phone=payload.sender,
            message_body=payload.body,
            recipient_phone=payload.receiver
        )
        return result
    except Exception as e:
        logger.error(f"Inbound SMS processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inbound processing failed: {e!s}"
        )


@router.post("/outbound", status_code=status.HTTP_200_OK)
async def send_outbound_sms(
    payload: OutboundSMSRequest,
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Sends an outbound SMS using the registry's registered providers.
    """
    logger.info(f"Request to send outbound SMS to {payload.recipient}")
    registry = container.sms_provider_registry

    # Select provider
    provider = None
    if payload.provider_id:
        provider = registry.discover(payload.provider_id)
    else:
        providers = registry.list_providers()
        if providers:
            provider = providers[0]

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active SMS provider available."
        )

    try:
        success = await provider.send_sms(payload.recipient, payload.body)
        return {"success": success, "provider_id": provider.id, "recipient": payload.recipient}
    except Exception as e:
        logger.error(f"Failed to dispatch outbound SMS: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dispatch outbound SMS: {e!s}"
        )


@router.get("/providers")
async def list_sms_providers(container: Container = Depends(get_container)) -> list[dict[str, Any]]:
    """Lists registered SMS providers."""
    providers = container.sms_provider_registry.list_providers()
    return [
        {
            "id": p.id,
            "version": p.version,
            "status": p.status.value,
            "capabilities": p.capabilities,
            "latency_ms": p.latency_ms
        }
        for p in providers
    ]


@router.get("/sessions")
async def list_sms_sessions(container: Container = Depends(get_container)) -> list[dict[str, Any]]:
    """Lists active SMS sessions."""
    sessions = container.sms_session_manager.list_sessions()
    return [s.model_dump() for s in sessions]


@router.get("/health")
async def sms_health(container: Container = Depends(get_container)) -> dict[str, Any]:
    """Retrieves health metrics for registered SMS providers."""
    return await container.sms_provider_registry.health_check()


@router.get("/status")
async def sms_status(container: Container = Depends(get_container)) -> dict[str, Any]:
    """Returns SMS platform global status and session cleanup telemetry counts."""
    expired_count = container.sms_session_manager.cleanup_expired()
    providers = container.sms_provider_registry.list_providers()
    return {
        "status": "healthy",
        "active_providers_count": len([p for p in providers if p.status.value == "active"]),
        "total_registered_providers": len(providers),
        "expired_sessions_cleaned": expired_count
    }
