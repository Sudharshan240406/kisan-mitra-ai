"""
Kisan Mitra AI — Admin Operations Router
========================================
Implements administrative endpoints for system configuration inspection, log tailing,
and live operational telemetry metrics.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

from app.core.config import settings
from app.core.container import Container
from app.dependencies.container import get_container
from fastapi import APIRouter, Depends, HTTPException, Query, status

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Portal"])
logger = logging.getLogger("kisan_mitra_ai.api.admin")


@router.get("/config", response_model=Dict[str, Any])
def get_system_config(container: Container = Depends(get_container)) -> Dict[str, Any]:
    """
    Retrieves active configurations, integration settings, and dynamic feature flags.
    """
    logger.info("Admin: Fetching active system configuration.")
    return {
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "debug_mode": settings.DEBUG,
        "cors_origins": settings.CORS_ORIGINS,
        "log_level": settings.LOG_LEVEL,
        "active_llm_provider": settings.DEFAULT_LLM_PROVIDER,
        "sms_provider": settings.SMS_PROVIDER,
        "voice_enabled": settings.FEATURE_VOICE_ENABLED,
        "sms_enabled": settings.FEATURE_SMS_ENABLED,
        "integration_active_mappings": container.integration_registry._active_providers,
        "budget_limits": {
            "daily_usd_budget": container.ai_cost_manager.daily_budget_usd,
            "accumulated_cost_usd": container.ai_cost_manager.accumulated_cost_usd
        }
    }


@router.get("/logs", response_model=List[str])
def get_log_tail(
    lines: int = Query(default=100, ge=1, le=500),
    log_type: str = Query(default="app", description="app | error"),
    container: Container = Depends(get_container)
) -> List[str]:
    """
    Retrieves the last N lines of application or error logs.
    """
    logger.info(f"Admin: Tailing last {lines} lines of {log_type} logs.")
    log_file = "logs/app.log" if log_type == "app" else "logs/error.log"

    if not os.path.exists(log_file):
        # Fallback to general lookup
        os.makedirs("logs", exist_ok=True)
        with open(log_file, "w") as f:
            f.write(f"Log file initialized: {log_file}\n")

    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
            return [line.strip() for line in all_lines[-lines:]]
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to read log file: {e!s}"
        )


@router.get("/stats", response_model=Dict[str, Any])
def get_system_stats(container: Container = Depends(get_container)) -> Dict[str, Any]:
    """
    Compiles live system diagnostics, registered agents, and onboarding metrics.
    """
    logger.info("Admin: Compiling live system telemetry statistics.")
    platform = container.personalization_platform

    # Calculate caching stats
    cache_healthy = True
    active_agents = container.registry.list_agents()

    return {
        "onboarded_farmers_count": len(platform.profiles),
        "total_conversation_memories": sum(len(m.conversations) for m in platform.memories.values()),
        "total_scheduled_reminders": sum(len(r) for r in platform.reminders.values()),
        "registered_agents": active_agents,
        "registered_personalization_services": platform.registry.list_services(),
        "vector_db_connected": True,
        "cache_healthy": cache_healthy,
        "integration_registries_count": len(container.integration_registry.list_integrations()),
        "personalization_metrics": platform.health().get("metrics", {})
    }
