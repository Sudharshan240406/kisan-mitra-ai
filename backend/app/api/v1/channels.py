from typing import Any

from app.channels.envelope import MessageEnvelope, ResponseEnvelope
from app.core.container import Container
from app.dependencies.container import get_container
from fastapi import APIRouter, Depends, Query

router = APIRouter(prefix="/api/v1/channels", tags=["Omnichannel"])


@router.post("/route", response_model=ResponseEnvelope)
async def route_message(
    envelope: MessageEnvelope,
    asynchronous: bool = Query(default=False, description="Process asynchronously in background"),
    container: Container = Depends(get_container)
) -> ResponseEnvelope:
    """
    Route an inbound message envelope through the channel framework.
    """
    return await container.channel_router.route_inbound(envelope, asynchronous=asynchronous)


@router.get("", response_model=list[dict[str, Any]])
async def list_registered_channels(
    container: Container = Depends(get_container)
) -> list[dict[str, Any]]:
    """
    Retrieve metadata for all registered communication channels.
    """
    channels = container.channel_registry.list_channels()
    return [ch.channel_metadata.model_dump() for ch in channels]


@router.get("/health", response_model=dict[str, Any])
async def check_channels_health(
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Query the operational health status across all channels.
    """
    return await container.channel_registry.health_check()


@router.post("/sessions/cleanup", response_model=dict[str, Any])
async def cleanup_expired_sessions(
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Trigger cleanup and expiration of timed-out communication sessions.
    """
    count = container.session_manager.cleanup_expired()
    return {
        "status": "success",
        "expired_sessions_cleaned": count
    }
