import logging
from typing import Any

from app.core.container import Container
from app.dependencies.container import get_container
from app.media.media import MediaInput, MediaMetadata, MediaType
from fastapi import APIRouter, Depends, File, Form, UploadFile

router = APIRouter(prefix="/api/v1/media", tags=["Media Intelligence"])
logger = logging.getLogger("kisan_mitra_ai.api.media")


@router.post("/upload", response_model=dict[str, Any])
async def upload_media(
    conversation_id: str = Form(..., description="Target conversation session ID"),
    media_type: MediaType = Form(..., description="Classification type of media input"),
    file: UploadFile = File(..., description="Raw binary file payload"),
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Ingest a media file, execute the extraction pipeline, perform policy safety checks,
    and route the extracted insights to the advisory engine.
    """
    logger.info(f"Ingesting media file '{file.filename}' of type '{media_type.value}' for conversation '{conversation_id}'")

    # Read binary content
    content_bytes = await file.read()
    file_size = len(content_bytes)

    # Extract format extension
    filename = file.filename or "unknown_file"
    fmt = filename.split(".")[-1] if "." in filename else "raw"

    # Build metadata
    metadata = MediaMetadata(
        file_size_bytes=file_size,
        format=fmt,
        mime_type=file.content_type
    )

    # Build input
    media_input = MediaInput(
        media_type=media_type,
        filename=filename,
        content=content_bytes,
        metadata=metadata
    )

    # Execute pipeline
    result = await container.media_pipeline.execute(media_input, conversation_id)
    return result


@router.get("/providers", response_model=list[dict[str, Any]])
async def list_media_providers(
    container: Container = Depends(get_container)
) -> list[dict[str, Any]]:
    """
    List all registered media processing providers and their configuration details.
    """
    providers = container.media_provider_registry.list_providers()
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


@router.get("/sessions", response_model=list[dict[str, Any]])
async def list_media_sessions(
    container: Container = Depends(get_container)
) -> list[dict[str, Any]]:
    """
    Retrieve logs for active media processing sessions.
    """
    sessions = container.media_session_manager.list_sessions()
    return [s.model_dump() for s in sessions]
