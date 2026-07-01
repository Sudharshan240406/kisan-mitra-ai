import logging
from typing import Any

from app.core.container import Container
from app.dependencies.container import get_container
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/v1/integrations", tags=["External Integrations"])
logger = logging.getLogger("kisan_mitra_ai.api.integrations")


@router.get("", response_model=list[dict[str, Any]])
async def list_integrations(
    container: Container = Depends(get_container)
) -> list[dict[str, Any]]:
    """
    List all registered external integrations, their status, configurations, and active mappings.
    """
    logger.info("Listing all registered external integrations.")
    registry = container.integration_registry
    res = []
    for integration in registry.list_integrations():
        meta = integration.metadata
        res.append({
            "id": meta.id,
            "name": meta.name,
            "version": meta.version,
            "description": meta.description,
            "type": meta.type,
            "status": meta.status,
            "capabilities": meta.capabilities,
            "configuration": meta.configuration,
            "feature_flags": meta.feature_flags,
            "is_active": registry._active_providers.get(meta.type) == meta.id
        })
    return res


@router.get("/metrics", response_model=dict[str, Any])
async def get_integration_metrics(
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Exposes external integration-specific telemetry measurements.
    """
    metrics = container.telemetry.export_metrics()
    return metrics.get("integration_metrics", {})


@router.post("/{integration_id}/toggle", response_model=dict[str, Any])
async def toggle_integration_status(
    integration_id: str,
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Toggles integration operational status between 'active' and 'inactive'.
    """
    try:
        integration = container.integration_registry.get(integration_id)
        meta = integration.metadata
        old_status = meta.status
        new_status = "inactive" if old_status == "active" else "active"
        meta.status = new_status

        # Log to governance
        container.governance_engine.register_artifact(
            artifact_type="integration",
            artifact_id=meta.id,
            version=meta.version,
            status=new_status
        )

        logger.info(f"Toggled integration '{integration_id}' status from '{old_status}' to '{new_status}'.")
        return {"status": "success", "integration_id": integration_id, "new_status": new_status}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found.")


@router.post("/{integration_id}/activate", response_model=dict[str, Any])
async def activate_integration_provider(
    integration_id: str,
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Activates an integration as the primary provider for its logical type.
    """
    try:
        integration = container.integration_registry.get(integration_id)
        meta = integration.metadata
        container.integration_registry.set_active(meta.type, integration_id)
        return {"status": "success", "integration_id": integration_id, "type": meta.type}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found.")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/{integration_id}/test", response_model=dict[str, Any])
async def test_integration(
    integration_id: str,
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Triggers a mock/live operation test run of the integration to collect telemetry/metrics.
    """
    try:
        integration = container.integration_registry.get(integration_id)
        meta = integration.metadata

        # Define dynamic test operations based on type
        test_ops = {
            "weather": lambda: integration.get_forecast("Ludhiana, Punjab"),
            "market": lambda: integration.get_market_price("Wheat", "Ludhiana Mandi"),
            "government": lambda: integration.list_schemes(),
            "storage": lambda: integration.write("test_key", "test_val"),
            "notifications": lambda: integration.send_notification("+919999999999", "Test Alert Message"),
            "authentication": lambda: integration.authenticate("admin", "valid-session-jwt-token")
        }

        func = test_ops.get(meta.type)
        if not func:
            raise HTTPException(status_code=400, detail=f"Cannot test integration type '{meta.type}'")

        # Execute resiliently
        result = await container.resilient_runner.execute(
            integration_id=meta.id,
            operation_name="test_operation",
            func=func,
            retries=1,
            timeout=2.0
        )

        return {"status": "success", "integration_id": integration_id, "result": str(result)}

    except KeyError:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found.")
    except Exception as e:
        logger.error(f"Test run failed for '{integration_id}': {e}")
        return {"status": "failed", "integration_id": integration_id, "error": str(e)}
