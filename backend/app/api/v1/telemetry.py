import logging
from typing import Any

from app.core.container import Container
from app.dependencies.container import get_container
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry Monitoring"])
logger = logging.getLogger("kisan_mitra_ai.api.telemetry")


@router.get("/metrics", response_model=dict[str, Any])
async def get_telemetry_metrics(
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Retrieve live platform telemetry performance metrics, latencies, and transaction totals.
    """
    logger.info("Exporting live platform telemetry metrics")
    return container.telemetry.export_metrics()
