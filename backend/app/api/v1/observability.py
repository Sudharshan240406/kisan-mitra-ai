import logging
from typing import Any, Dict, List, cast

from app.core.container import Container
from app.dependencies.container import get_container
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v1/observability", tags=["Enterprise Observability"])
logger = logging.getLogger("kisan_mitra_ai.api.observability")

@router.get("/metrics", response_model=Dict[str, Any])
def get_metrics(
    container: Container = Depends(get_container)
) -> Dict[str, Any]:
    """
    Exposes aggregated system and execution metrics.
    """
    logger.info("Fetching aggregated observability metrics")
    return cast(Dict[str, Any], container.observability_manager.metrics())

@router.get("/health", response_model=Dict[str, Any])
async def get_health(
    container: Container = Depends(get_container)
) -> Dict[str, Any]:
    """
    Queries and returns live health status for all system dependencies.
    """
    logger.info("Executing live health status audit for all components")
    return cast(Dict[str, Any], await container.observability_manager.health())

@router.get("/traces", response_model=List[Dict[str, Any]])
def get_traces(
    container: Container = Depends(get_container)
) -> List[Dict[str, Any]]:
    """
    Returns recorded tracing spans.
    """
    logger.info("Retrieving collected distributed traces")
    return cast(List[Dict[str, Any]], container.observability_manager.traces())

@router.get("/system_status", response_model=Dict[str, Any])
def get_system_status(
    container: Container = Depends(get_container)
) -> Dict[str, Any]:
    """
    Retrieves system performance, memory usage, and execution metrics.
    """
    logger.info("Retrieving CPU and Memory system status")
    return cast(Dict[str, Any], container.observability_manager.system_status())
