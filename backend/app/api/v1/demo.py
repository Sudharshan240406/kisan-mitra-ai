"""
Kisan Mitra AI — Demo API Endpoints (Phase 16: Fully Wired)
============================================================
End-to-end simulation with all 13 required WebSocket events,
error recovery, performance optimizations, and the full pipeline:

  CALL_STARTED → CALLER_IDENTIFIED → DIGITAL_TWIN_LOADED →
  SCHEME_SEARCH_STARTED → SCHEME_MATCHED (×N) → ELIGIBILITY_COMPLETED →
  REASONING_COMPLETED → DOCUMENT_ADVISOR_READY → VOICE_RESPONSE_STARTED →
  TRANSCRIPT_UPDATED (×N) → CALL_COMPLETED

Error path:
  CALL_ERROR → ERROR_RECOVERY_STARTED

Demo lifecycle:
  DEMO_STARTED → DEMO_PROGRESS → DEMO_FARMER_COMPLETE (×6) → DEMO_COMPLETED
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

# Service instances (module-level singletons — fast after first call)
_demo_service = DemoService()
_eligibility_engine = EligibilityEngine()
_document_advisor = DocumentAdvisor()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Farmer Profile Endpoints
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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


@router.get("/schemes/{farmer_id}", response_model=dict[str, Any])
async def get_farmer_scheme_eligibility(farmer_id: str) -> dict[str, Any]:
    """
    Returns full eligibility breakdown for all 11 government schemes
    for a specific demo farmer. Supports judge inspection of the engine.
    """
    farmer = _demo_service.get_farmer(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail=f"Demo farmer '{farmer_id}' not found.")

    from app.knowledge.modules.government import GovernmentKnowledgeProvider
    gov_provider = GovernmentKnowledgeProvider()
    all_schemes = gov_provider.get_all_schemes()

    recommendations = _eligibility_engine.evaluate_all(farmer, all_schemes)
    eligible = [r for r in recommendations if r.status == "ELIGIBLE"]
    possibly = [r for r in recommendations if r.status == "POSSIBLY_ELIGIBLE"]

    return {
        "farmer_id": farmer_id,
        "farmer_name": farmer.name,
        "total_schemes_evaluated": len(recommendations),
        "eligible_count": len(eligible),
        "possibly_eligible_count": len(possibly),
        "recommendations": [r.model_dump() for r in recommendations],
        "engine_health": _eligibility_engine.health(),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Core Simulation: Full Pipeline with All 13 WebSocket Events
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from fastapi import Depends
from app.dependencies.container import get_container
from app.core.container import Container

@router.post("/simulate-call/{farmer_id}", response_model=dict[str, Any])
async def simulate_call(
    farmer_id: str,
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Simulate a complete IVR call for a demo farmer.

    Emits the full 13-event sequence via WebSocket:
      CALL_STARTED → CALLER_IDENTIFIED → DIGITAL_TWIN_LOADED →
      SCHEME_SEARCH_STARTED → SCHEME_MATCHED (×N) → ELIGIBILITY_COMPLETED →
      REASONING_COMPLETED → DOCUMENT_ADVISOR_READY → VOICE_RESPONSE_STARTED →
      TRANSCRIPT_UPDATED (×N) → CALL_COMPLETED

    Error path emits: CALL_ERROR → ERROR_RECOVERY_STARTED
    """
    farmer = _demo_service.get_farmer(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail=f"Demo farmer '{farmer_id}' not found.")

    # Import here to avoid circular imports at module load
    from app.api.v1.websocket import ws_manager
    from app.knowledge.modules.government import GovernmentKnowledgeProvider

    call_id = f"DEMO-CALL-{farmer_id}-{int(time.time())}"
    start_time = time.perf_counter()

    try:
        # ── Event 1: CALL_STARTED ──────────────────────────────────────────
        await ws_manager.push_event("CALL_STARTED", {
            "call_id": call_id,
            "farmer_id": farmer_id,
            "phone": farmer.phone_number,
            "language": farmer.preferred_language,
            "timestamp": time.time(),
        })
        await asyncio.sleep(0.25)

        # ── Event 2: CALLER_IDENTIFIED ────────────────────────────────────
        await ws_manager.push_event("CALLER_IDENTIFIED", {
            "call_id": call_id,
            "farmer_id": farmer_id,
            "farmer_name": farmer.name,
            "phone": farmer.phone_number,
            "state": farmer.state,
            "district": farmer.district,
            "lookup_method": "phone_registry",
        })
        await asyncio.sleep(0.2)

        # ── Event 3: DIGITAL_TWIN_LOADED ──────────────────────────────────
        farmer_summary = _demo_service.get_farmer_summary(farmer)
        digital_twin_snapshot = {
            **farmer_summary,
            "digital_twin_version": "v2.0",
            "profile_completeness": _compute_profile_completeness(farmer),
            "last_interaction": "First call" if farmer.metadata.get("calls_count", 0) == 0 else "Returning farmer",
            "risk_profile": _compute_risk_profile(farmer),
        }
        await ws_manager.push_event("DIGITAL_TWIN_LOADED", {
            "call_id": call_id,
            "farmer_id": farmer_id,
            "digital_twin": digital_twin_snapshot,
        })
        await asyncio.sleep(0.2)

        # ── Event 4: SCHEME_SEARCH_STARTED ───────────────────────────────
        gov_provider = GovernmentKnowledgeProvider()
        all_schemes = gov_provider.get_all_schemes()
        await ws_manager.push_event("SCHEME_SEARCH_STARTED", {
            "call_id": call_id,
            "farmer_id": farmer_id,
            "total_schemes": len(all_schemes),
            "engine": "EligibilityEngine v2.0",
        })
        await asyncio.sleep(0.15)

        # ── Evaluate all schemes (core engine call) ───────────────────────
        recommendations = _eligibility_engine.evaluate_all(farmer, all_schemes)

        # ── Events 5…N: SCHEME_MATCHED (one per scheme, streamed) ─────────
        for rec in recommendations:
            await ws_manager.push_event("SCHEME_MATCHED", {
                "call_id": call_id,
                "scheme_id": rec.scheme_id,
                "title": rec.title,
                "status": rec.status,
                "confidence": round(rec.confidence, 3),
                "benefits": rec.benefits,
            })
            await asyncio.sleep(0.05)  # fast streaming — judges see each scheme resolve

        # ── Event N+1: ELIGIBILITY_COMPLETED ──────────────────────────────
        eligible = [r for r in recommendations if r.status == "ELIGIBLE"]
        possibly = [r for r in recommendations if r.status == "POSSIBLY_ELIGIBLE"]
        await ws_manager.push_event("ELIGIBILITY_COMPLETED", {
            "call_id": call_id,
            "total_evaluated": len(recommendations),
            "eligible_count": len(eligible),
            "possibly_eligible_count": len(possibly),
            "top_scheme": eligible[0].title if eligible else None,
            "results": [
                {
                    "scheme_id": r.scheme_id,
                    "title": r.title,
                    "status": r.status,
                    "confidence": round(r.confidence, 3),
                }
                for r in recommendations
            ],
        })
        await asyncio.sleep(0.2)

        # ── Event N+2: REASONING_COMPLETED ───────────────────────────────
        doc_guidance: dict[str, Any] = {}
        voice_text = ""
        top_rec = eligible[0] if eligible else (possibly[0] if possibly else None)

        if top_rec:
            import json
            try:
                from agents.schemes.schemes import GovernmentSchemeAgent
                from app.schemas.requests import AgentRequest
                from app.core.context import AgentContext
                from app.services.scheme_service import GovernmentSchemeService

                agent_context = AgentContext(
                    request_id=call_id,
                    trace_id=call_id,
                    session_id=call_id,
                    farmer_id=farmer_id,
                    language=farmer.preferred_language
                )
                agent_context.metadata["container"] = container

                scheme_service = GovernmentSchemeService()
                scheme_agent = GovernmentSchemeAgent(container.llm_provider, scheme_service)
                agent_result = await scheme_agent.execute(AgentRequest(query="schemes"), agent_context)

                ai_data = json.loads(agent_result.content)
                explanation_val = ai_data.get("explanation", "")
                if not explanation_val:
                    explanation_list = top_rec.reasoning
                elif isinstance(explanation_val, list):
                    explanation_list = [str(x) for x in explanation_val]
                else:
                    explanation_list = [s.strip() for s in explanation_val.split(".") if s.strip()]

                explanation_list = [f"✓ Rule-Based Engine: Eligible for {top_rec.title}"] + explanation_list
                voice_text = ai_data.get("voice_summary", "")
            except Exception as e:
                logger.error(f"Failed to generate Gemini explanation in demo: {e}")
                explanation_list = top_rec.reasoning
                voice_text = ""

            await ws_manager.push_event("REASONING_COMPLETED", {
                "call_id": call_id,
                "top_scheme": top_rec.title,
                "scheme_id": top_rec.scheme_id,
                "reasoning": explanation_list,
                "evidence": top_rec.evidence,
                "confidence": round(top_rec.confidence, 3),
                "benefits": top_rec.benefits,
                "helpline": top_rec.helpline,
                "deadline": top_rec.deadline,
            })
            await asyncio.sleep(0.2)

            # ── Event N+3: DOCUMENT_ADVISOR_READY ─────────────────────────
            doc_guidance = _document_advisor.generate_guidance(farmer, top_rec)
            await ws_manager.push_event("DOCUMENT_ADVISOR_READY", {
                "call_id": call_id,
                "scheme_id": top_rec.scheme_id,
                "required_documents": doc_guidance.get("required_documents", []),
                "missing_documents": doc_guidance.get("missing_documents", []),
                "tips": doc_guidance.get("tips", []),
                "nearest_office": doc_guidance.get("nearest_office", "Contact local agriculture office"),
                "helpline": top_rec.helpline,
                "application_steps": doc_guidance.get("application_steps", []),
            })
            await asyncio.sleep(0.2)

            # ── Event N+4: VOICE_RESPONSE_STARTED ─────────────────────────
            if not voice_text:
                voice_text = _document_advisor.generate_voice_summary(
                    farmer, top_rec, farmer.preferred_language
                )
            await ws_manager.push_event("VOICE_RESPONSE_STARTED", {
                "call_id": call_id,
                "text": voice_text,
                "language": farmer.preferred_language,
                "scheme_id": top_rec.scheme_id,
                "tts_provider": "mock-tts",
            })
            await asyncio.sleep(0.2)
        else:
            voice_text = "कोई उपयुक्त योजना नहीं मिली। कृपया नजदीकी कृषि कार्यालय से संपर्क करें।"
            await ws_manager.push_event("VOICE_RESPONSE_STARTED", {
                "call_id": call_id,
                "text": voice_text,
                "language": farmer.preferred_language,
                "tts_provider": "mock-tts",
            })

        # ── Events N+5…M: TRANSCRIPT_UPDATED (streamed, faster delays) ───
        rec_dicts = [r.model_dump() for r in recommendations]
        transcript = _demo_service.generate_call_transcript(farmer, rec_dicts)
        for turn in transcript:
            await ws_manager.push_event("TRANSCRIPT_UPDATED", {
                "call_id": call_id,
                "role": turn["role"],
                "text": turn["text"],
                "timestamp": time.time(),
            })
            await asyncio.sleep(0.08)  # 80ms per turn — fast enough for demo

        # ── Final: CALL_COMPLETED ─────────────────────────────────────────
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
        await ws_manager.push_event("CALL_COMPLETED", {
            "call_id": call_id,
            "farmer_id": farmer_id,
            "farmer_name": farmer.name,
            "duration_ms": elapsed_ms,
            "eligible_schemes": len(eligible),
            "top_scheme": top_rec.title if top_rec else None,
            "performance_grade": "A" if elapsed_ms < 5000 else "B",
        })

        return {
            "success": True,
            "call_id": call_id,
            "farmer": farmer_summary,
            "digital_twin": digital_twin_snapshot,
            "recommendations": rec_dicts,
            "eligible_count": len(eligible),
            "top_scheme": top_rec.title if top_rec else None,
            "document_guidance": doc_guidance,
            "voice_response": voice_text,
            "transcript": transcript,
            "elapsed_ms": elapsed_ms,
            "performance_grade": "A" if elapsed_ms < 5000 else "B",
        }

    except Exception as exc:
        # ── Error Path: CALL_ERROR + ERROR_RECOVERY_STARTED ───────────────
        logger.error(f"[simulate_call] Pipeline error for farmer '{farmer_id}': {exc}", exc_info=True)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)

        await ws_manager.push_event("CALL_ERROR", {
            "call_id": call_id,
            "farmer_id": farmer_id,
            "error": str(exc),
            "elapsed_ms": elapsed_ms,
        })
        await asyncio.sleep(0.1)
        await ws_manager.push_event("ERROR_RECOVERY_STARTED", {
            "call_id": call_id,
            "recovery_action": "fallback_to_helpline",
            "helpline": "1800-180-1551",
            "message": "हमारे सिस्टम में कुछ समस्या है। कृपया 1800-180-1551 पर कॉल करें।",
        })

        return {
            "success": False,
            "call_id": call_id,
            "error": str(exc),
            "recovery_action": "fallback_to_helpline",
            "helpline": "1800-180-1551",
            "elapsed_ms": elapsed_ms,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Multi-Farmer Demo: Full Hackathon Showcase
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/start", response_model=dict[str, Any])
async def start_demo() -> dict[str, Any]:
    """
    Start a complete multi-farmer demo simulation.
    Cycles through all 6 demo farmers sequentially.
    Emits DEMO_STARTED, DEMO_PROGRESS, DEMO_FARMER_COMPLETE, DEMO_COMPLETED.
    Total estimated runtime: 5–7 minutes.
    """
    from app.api.v1.websocket import ws_manager

    farmers = _demo_service.get_all_farmers()
    results: list[dict[str, Any]] = []

    await ws_manager.push_event("DEMO_STARTED", {
        "total_farmers": len(farmers),
        "estimated_duration_minutes": 6,
        "farmers": [_demo_service.get_farmer_summary(f) for f in farmers],
    })

    for i, farmer in enumerate(farmers):
        # Notify dashboard: next farmer starting
        await ws_manager.push_event("DEMO_PROGRESS", {
            "current": i + 1,
            "total": len(farmers),
            "farmer_id": farmer.farmer_id,
            "farmer_name": farmer.name,
            "state": farmer.state,
        })
        await asyncio.sleep(0.3)

        # Run the full simulation pipeline
        result = await simulate_call(farmer.farmer_id)
        results.append({
            "farmer_id": farmer.farmer_id,
            "farmer_name": farmer.name,
            "eligible_count": result.get("eligible_count", 0),
            "top_scheme": result.get("top_scheme"),
            "elapsed_ms": result.get("elapsed_ms", 0),
            "success": result.get("success", False),
        })

        # Notify dashboard: this farmer's call completed
        await ws_manager.push_event("DEMO_FARMER_COMPLETE", {
            "current": i + 1,
            "total": len(farmers),
            "farmer_id": farmer.farmer_id,
            "farmer_name": farmer.name,
            "eligible_count": result.get("eligible_count", 0),
            "top_scheme": result.get("top_scheme"),
        })

        # Brief pause between farmers for dashboard visibility
        if i < len(farmers) - 1:
            await asyncio.sleep(2.0)

    await ws_manager.push_event("DEMO_COMPLETED", {
        "total_farmers": len(farmers),
        "results": results,
        "total_eligible_determinations": sum(r["eligible_count"] for r in results),
    })

    return {
        "success": True,
        "total_farmers": len(farmers),
        "results": results,
    }


@router.get("/status", response_model=dict[str, Any])
async def demo_status() -> dict[str, Any]:
    """Get demo mode status and engine health."""
    from app.api.v1.websocket import ws_manager
    return {
        "demo_mode": True,
        "total_farmers": len(_demo_service.get_all_farmers()),
        "engine_health": _eligibility_engine.health(),
        "ws_connected_clients": ws_manager.client_count,
        "available_endpoints": [
            "GET  /api/v1/demo/farmers",
            "GET  /api/v1/demo/farmers/{id}",
            "GET  /api/v1/demo/schemes/{id}",
            "POST /api/v1/demo/simulate-call/{id}",
            "POST /api/v1/demo/start",
            "GET  /api/v1/demo/status",
        ],
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Internal Helpers (not exposed via API)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _compute_profile_completeness(farmer: Farmer) -> int:
    """Compute profile completeness percentage (0–100) for Digital Twin panel."""
    fields = [
        farmer.name, farmer.phone_number, farmer.state, farmer.district,
        farmer.land_size_hectares, farmer.farmer_category, farmer.gender,
        farmer.preferred_language, farmer.active_crops,
    ]
    optional = [
        farmer.soil_type, farmer.water_source, farmer.caste_category,
        farmer.income_bracket, farmer.has_bank_account, farmer.has_aadhaar,
        farmer.is_organic,
    ]
    core_score = sum(1 for f in fields if f is not None and f != [] and f != "") / len(fields)
    opt_score = sum(1 for f in optional if f is not None) / len(optional)
    return round((core_score * 0.7 + opt_score * 0.3) * 100)


def _compute_risk_profile(farmer: Farmer) -> str:
    """Simple risk assessment for Digital Twin enrichment."""
    risk_score = 0
    if farmer.recent_damage:
        risk_score += 3
    if farmer.farmer_category in ("Marginal", "Small"):
        risk_score += 2
    if farmer.income_bracket and "Below" in farmer.income_bracket:
        risk_score += 1
    if not farmer.has_aadhaar or not farmer.has_bank_account:
        risk_score += 2
    if farmer.is_tenant:
        risk_score += 1
    if risk_score >= 6:
        return "HIGH"
    elif risk_score >= 3:
        return "MEDIUM"
    return "LOW"
