import logging
from typing import Any, Optional

from app.core.container import Container
from app.dependencies.container import get_container
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.api.v1.ai")
router = APIRouter()

class BudgetUpdateRequest(BaseModel):
    daily_budget_usd: float = Field(..., gt=0.0, description="New daily AI model platform budget cap limit.")

class ModelToggleRequest(BaseModel):
    model_id: str = Field(..., description="Target model identifier.")
    availability: str = Field(..., description="Status string: healthy, degraded, offline.")

class DiagnosticRequest(BaseModel):
    prompt: str = Field(default="Hello Kisan Mitra. What crops are best in monsoon?", description="Diagnostic input query.")
    task_type: str = Field(default="advisory", description="Query context task type.")
    preferred_provider: Optional[str] = Field(default=None, description="Force selection constraint.")

@router.get("/providers", tags=["AI Platform"])
def list_providers(container: Container = Depends(get_container)) -> list[dict[str, Any]]:
    """
    Returns all registered AI models catalog details and pricing specs.
    """
    models = container.ai_registry.list_models()
    result = []
    for m in models:
        result.append({
            "model_id": m.model_id,
            "provider_name": m.provider_name,
            "capabilities": m.capabilities,
            "cost_per_million_input": m.cost_per_million_input,
            "cost_per_million_output": m.cost_per_million_output,
            "context_window": m.context_window,
            "average_latency_ms": m.average_latency_ms,
            "reliability_rate": m.reliability_rate,
            "availability": m.availability,
            "status": m.status
        })
    return result

@router.get("/summary", tags=["AI Platform"])
def get_cost_summary(container: Container = Depends(get_container)) -> dict[str, Any]:
    """
    Retrieves current budget usage counters, error rates, and total token tallies.
    """
    return container.ai_cost_manager.get_summary()

@router.post("/budget", tags=["AI Platform"])
def update_budget(req: BudgetUpdateRequest, container: Container = Depends(get_container)) -> dict[str, str]:
    """
    Updates the daily budget cap limits dynamically.
    """
    container.ai_cost_manager.daily_budget_usd = req.daily_budget_usd
    return {"message": f"Daily AI budget threshold successfully updated to: ${req.daily_budget_usd:.2f}"}

@router.post("/toggle", tags=["AI Platform"])
def toggle_model_status(req: ModelToggleRequest, container: Container = Depends(get_container)) -> dict[str, str]:
    """
    Toggles the operational health status of a target model adapter.
    """
    specs = container.ai_registry.get_specs(req.model_id)
    if not specs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model ID '{req.model_id}' is not registered in the system catalog."
        )
    container.ai_registry.update_status(req.model_id, req.availability)
    return {"message": f"Model '{req.model_id}' health status successfully changed to '{req.availability}'."}

@router.post("/test", tags=["AI Platform"])
def run_diagnostic_test(req: DiagnosticRequest, container: Container = Depends(get_container)) -> dict[str, Any]:
    """
    Triggers a live or mock diagnostic request tracking exact latency, tokens, and routing cascades.
    """
    start_time = float(time_now_getter())
    try:
        # Resolve target model using router
        budget_left = container.ai_cost_manager.daily_budget_usd - container.ai_cost_manager.accumulated_cost_usd
        model_id, reason, confidence = container.ai_router.select_model(
            task_type=req.task_type,
            prompt_size=len(req.prompt),
            budget_remaining=budget_left,
            preferred_provider=req.preferred_provider
        )

        adapter = container.ai_registry.get_adapter(model_id)
        if not adapter:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Adapter missing for selected model '{model_id}'."
            )

        # Force execute adapter to fetch response metadata
        response = adapter.generate(req.prompt, task_type=req.task_type)
        latency = (float(time_now_getter()) - start_time) * 1000.0
        response.latency_ms = latency

        # Track usage in database
        cost = container.ai_cost_manager.record_usage(
            model_id=model_id,
            input_tokens=response.prompt_tokens,
            output_tokens=response.completion_tokens
        )
        response.cost = cost

        # Return full payload trace
        return {
            "status": "success",
            "routing": {
                "selected_model": model_id,
                "reason": reason,
                "confidence": confidence
            },
            "response": response.model_dump()
        }
    except Exception as e:
        logger.error(f"Diagnostic prompt run failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def time_now_getter() -> float:
    import time
    return time.time()
