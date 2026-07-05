"""
Kisan Mitra AI — Demo API Endpoints
======================================
Provides demo simulation endpoints for judge demonstrations.

Endpoints:
  GET  /api/v1/demo/farmers            — List all demo farmer profiles
  GET  /api/v1/demo/farmers/{id}       — Get a specific demo farmer
  POST /api/v1/demo/simulate-call/{id} — Simulate a full IVR call with live events
  POST /api/v1/demo/start              — Start a complete multi-farmer demo
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException

from app.models.farmer import Farmer
from app.services.demo import DemoService
from app.services.eligibility import EligibilityEngine
from app.services.document_advisor import DocumentAdvisor

logger = logging.getLogger("kisan_mitra_ai.api.demo")

router = APIRouter(prefix="/api/v1/demo", tags=["Demo & Simulation"])

# Service instances
_demo_service = DemoService()
_eligibility_engine = EligibilityEngine()
_document_advisor = DocumentAdvisor()


@router.get("/farmers", response_model=list[dict[str, Any]])
async def list_demo_farmers() -> list[dict[str, Any]]:
    """List all demo farmer profiles with summaries."""
    farmers = _demo_service.get_all_farmers()
    return [_demo_service.get_farmer_summary(f) for f in farmers]


@router.get("/farmers/{farmer_id}", response_model=dict[str, Any])
async def get_demo_farmer(farmer_id: str) -> dict[str, Any]:
    """Get a specific demo farmer profile."""
    farmer = _demo_service.get_farmer(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail=f"Demo farmer '{farmer_id}' not found.")
    return _demo_service.get_farmer_summary(farmer)


@router.post("/simulate-call/{farmer_id}", response_model=dict[str, Any])
async def simulate_call(farmer_id: str) -> dict[str, Any]:
    """
    Simulate a complete IVR call for a demo farmer.
    Evaluates eligibility, generates transcript, and streams events via WebSocket.
    """
    farmer = _demo_service.get_farmer(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail=f"Demo farmer '{farmer_id}' not found.")

    start_time = time.perf_counter()

    # Import here to avoid circular imports
    from app.api.v1.websocket import ws_manager
    from app.knowledge.modules.government import GovernmentKnowledgeProvider

    gov_provider = GovernmentKnowledgeProvider()
    all_schemes = gov_provider.get_all_schemes()

    # Stream CALL_STARTED
    await ws_manager.push_event("CALL_STARTED", {
        "call_id": f"DEMO-CALL-{farmer_id}",
        "farmer_id": farmer_id,
        "farmer_name": farmer.name,
        "phone": farmer.phone_number,
        "district": farmer.district,
        "state": farmer.state,
    })
    await asyncio.sleep(0.3)

    # Stream FARMER_IDENTIFIED
    await ws_manager.push_event("FARMER_IDENTIFIED", {
        "call_id": f"DEMO-CALL-{farmer_id}",
        "farmer": _demo_service.get_farmer_summary(farmer),
    })
    await asyncio.sleep(0.3)

    # Stream SCHEME_MATCHING
    await ws_manager.push_event("SCHEME_MATCHING", {
        "call_id": f"DEMO-CALL-{farmer_id}",
        "total_schemes": len(all_schemes),
        "status": "evaluating",
    })
    await asyncio.sleep(0.2)

    # Evaluate eligibility
    recommendations = _eligibility_engine.evaluate_all(farmer, all_schemes)
    rec_dicts = [r.model_dump() for r in recommendations]

    # Stream ELIGIBILITY_COMPLETE
    eligible = [r for r in recommendations if r.status == "ELIGIBLE"]
    await ws_manager.push_event("ELIGIBILITY_COMPLETE", {
        "call_id": f"DEMO-CALL-{farmer_id}",
        "total_evaluated": len(recommendations),
        "eligible_count": len(eligible),
        "results": [{"scheme_id": r.scheme_id, "title": r.title, "status": r.status, "confidence": r.confidence} for r in recommendations],
    })
    await asyncio.sleep(0.2)

    # Stream REASONING_COMPLETE
    if eligible:
        top = eligible[0]
        await ws_manager.push_event("REASONING_COMPLETE", {
            "call_id": f"DEMO-CALL-{farmer_id}",
            "top_scheme": top.title,
            "reasoning": top.reasoning,
            "evidence": top.evidence,
            "confidence": top.confidence,
        })
        await asyncio.sleep(0.2)

        # Generate document guidance
        doc_guidance = _document_advisor.generate_guidance(farmer, top)

        # Stream VOICE_RESPONSE_STARTED
        voice_text = _document_advisor.generate_voice_summary(farmer, top, farmer.preferred_language)
        await ws_manager.push_event("VOICE_RESPONSE_STARTED", {
            "call_id": f"DEMO-CALL-{farmer_id}",
            "text": voice_text,
            "language": farmer.preferred_language,
        })
        await asyncio.sleep(0.3)
    else:
        doc_guidance = {}
        voice_text = "No eligible schemes found."

    # Generate transcript
    transcript = _demo_service.generate_call_transcript(farmer, rec_dicts)

    # Stream transcript lines
    for turn in transcript:
        await ws_manager.push_event("TRANSCRIPT_UPDATED", {
            "call_id": f"DEMO-CALL-{farmer_id}",
            "role": turn["role"],
            "text": turn["text"],
        })
        await asyncio.sleep(0.15)

    # Stream CALL_COMPLETED
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    await ws_manager.push_event("CALL_COMPLETED", {
        "call_id": f"DEMO-CALL-{farmer_id}",
        "farmer_name": farmer.name,
        "duration_ms": round(elapsed_ms, 1),
        "eligible_schemes": len(eligible),
    })

    return {
        "success": True,
        "call_id": f"DEMO-CALL-{farmer_id}",
        "farmer": _demo_service.get_farmer_summary(farmer),
        "recommendations": rec_dicts,
        "document_guidance": doc_guidance,
        "voice_response": voice_text,
        "transcript": transcript,
        "elapsed_ms": round(elapsed_ms, 1),
    }


@router.post("/start", response_model=dict[str, Any])
async def start_demo() -> dict[str, Any]:
    """
    Start a complete multi-farmer demo simulation.
    Runs through all 6 demo farmers sequentially with delays for dashboard viewing.
    Total runtime: ~5-7 minutes.
    """
    from app.api.v1.websocket import ws_manager

    farmers = _demo_service.get_all_farmers()
    results: list[dict[str, Any]] = []

    await ws_manager.push_event("DEMO_STARTED", {
        "total_farmers": len(farmers),
        "estimated_duration_minutes": 6,
    })

    for i, farmer in enumerate(farmers):
        await ws_manager.push_event("DEMO_PROGRESS", {
            "current": i + 1,
            "total": len(farmers),
            "farmer_name": farmer.name,
        })

        # Simulate the call
        result = await simulate_call(farmer.farmer_id)
        results.append({
            "farmer_id": farmer.farmer_id,
            "farmer_name": farmer.name,
            "eligible_count": len([r for r in result.get("recommendations", []) if r.get("status") == "ELIGIBLE"]),
            "elapsed_ms": result.get("elapsed_ms", 0),
        })

        # Wait between calls for dashboard visibility
        if i < len(farmers) - 1:
            await asyncio.sleep(2.0)

    await ws_manager.push_event("DEMO_COMPLETED", {
        "total_farmers": len(farmers),
        "results": results,
    })

    return {
        "success": True,
        "total_farmers": len(farmers),
        "results": results,
    }
