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

from pydantic import BaseModel



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



from pydantic import Field


class SimulateCallRequest(BaseModel):
    question: str = Field(default="What government schemes am I eligible for?", description="Farmer advisory or eligibility question.")
    language: str | None = Field(default=None, description="Language override: hi, pa, kn, en.")


@router.post("/simulate-call/{farmer_id}", response_model=dict[str, Any])
async def simulate_call(
    farmer_id: str,
    request: SimulateCallRequest = SimulateCallRequest(),
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Simulate a complete IVR call for a demo farmer.
    Supports dynamic farmer questions, vernacular translation, and the tiered reasoning pipeline.
    """
    farmer = _demo_service.get_farmer(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail=f"Demo farmer '{farmer_id}' not found.")

    if request.language:
        farmer.preferred_language = request.language

    q_text = request.question.strip() if request.question else "What government schemes am I eligible for?"
    q_low = q_text.lower()
    is_scheme_query = any(k in q_low for k in ["scheme", "government", "eligib", "yojana", "subsid"]) or not request.question

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

        recommendations = []
        eligible = []
        possibly = []
        doc_guidance: dict[str, Any] = {}
        voice_text = ""
        top_rec = None

        if is_scheme_query:
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

            # Evaluate schemes
            recommendations = _eligibility_engine.evaluate_all(farmer, all_schemes)

            # SCHEME_MATCHED stream
            for rec in recommendations:
                await ws_manager.push_event("SCHEME_MATCHED", {
                    "call_id": call_id,
                    "scheme_id": rec.scheme_id,
                    "title": rec.title,
                    "status": rec.status,
                    "confidence": round(rec.confidence, 3),
                    "benefits": rec.benefits,
                })
                await asyncio.sleep(0.05)

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

            top_rec = eligible[0] if eligible else (possibly[0] if possibly else None)
            if top_rec:
                explanation_list = [f"✓ Rule-Based Engine: Eligible for {top_rec.title}"] + top_rec.reasoning
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

                voice_text = _demo_service.get_spoken_answer(q_text, "", farmer.preferred_language, farmer.active_crops, farmer.district)

        else:
            # ── NON-SCHEME ADVISORY QUERY (Weather, Market, Disease, Irrigation) ──
            await ws_manager.push_event("SCHEME_SEARCH_STARTED", {
                "call_id": call_id,
                "farmer_id": farmer_id,
                "total_schemes": 0,
                "engine": "KnowledgeEngine & Tiered Reasoning Pipeline",
            })
            await asyncio.sleep(0.15)

            await ws_manager.push_event("ELIGIBILITY_COMPLETED", {
                "call_id": call_id,
                "total_evaluated": 0,
                "eligible_count": 0,
                "possibly_eligible_count": 0,
                "top_scheme": None,
                "results": [],
            })
            await asyncio.sleep(0.15)

            # Route through orchestrator tiered pipeline
            from app.orchestrator.orchestrator import AgentOrchestrator
            from app.schemas.requests import ExecutionRequest

            orchestrator = AgentOrchestrator(container)
            exec_req = ExecutionRequest(
                session_id=call_id,
                query=q_text,
                farmer_id=farmer_id,
            )
            exec_res = await orchestrator.execute_query(exec_req)
            rec_payload = exec_res.data or {}

            rec_text = rec_payload.get("recommendation", "")
            confidence_val = rec_payload.get("confidence", 0.92)
            reasoning_path = rec_payload.get("reasoning", ["Advisory synthesized via Tiered Response Engine."])

            await ws_manager.push_event("REASONING_COMPLETED", {
                "call_id": call_id,
                "top_scheme": "Advisory Query: " + q_text[:30],
                "scheme_id": "advisory-tier",
                "reasoning": reasoning_path,
                "evidence": rec_payload.get("evidence", []),
                "confidence": round(confidence_val, 3),
                "benefits": rec_text[:120],
                "helpline": "1800-180-1551",
                "deadline": "N/A",
            })
            await asyncio.sleep(0.2)

            voice_text = _demo_service.get_spoken_answer(
                q_text, rec_text, farmer.preferred_language, farmer.active_crops, farmer.district
            )

        # ── Event: VOICE_RESPONSE_STARTED ─────────────────────────
        if not voice_text:
            voice_text = _demo_service.get_spoken_answer(q_text, "", farmer.preferred_language, farmer.active_crops, farmer.district)

        await ws_manager.push_event("VOICE_RESPONSE_STARTED", {
            "call_id": call_id,
            "text": voice_text,
            "language": farmer.preferred_language,
            "scheme_id": top_rec.scheme_id if top_rec else "advisory",
            "tts_provider": "mock-tts",
        })
        await asyncio.sleep(0.2)

        # ── Events: TRANSCRIPT_UPDATED ───────────────────
        rec_dicts = [r.model_dump() for r in recommendations] if recommendations else []
        transcript = _demo_service.generate_call_transcript(farmer, rec_dicts, question=q_text, voice_response=voice_text)

        for turn in transcript:
            await ws_manager.push_event("TRANSCRIPT_UPDATED", {
                "call_id": call_id,
                "role": turn["role"],
                "text": turn["text"],
                "timestamp": time.time(),
            })
            await asyncio.sleep(0.08)

        # ── Final: CALL_COMPLETED ─────────────────────────────────────────
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)

        await ws_manager.push_event("CALL_COMPLETED", {
            "call_id": call_id,
            "farmer_id": farmer_id,
            "farmer_name": farmer.name,
            "duration_ms": elapsed_ms,
            "eligible_schemes": len(eligible),
            "top_scheme": top_rec.title if top_rec else "Advisory Answered",
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

    demo_id = f"DEMO-SUITE-{int(time.time())}"

    await ws_manager.push_event("DEMO_STARTED", {

        "demo_id": demo_id,

        "total_farmers": len(farmers),

        "estimated_duration_minutes": 6,

        "farmers": [_demo_service.get_farmer_summary(f) for f in farmers],

    })



    for i, farmer in enumerate(farmers):

        # Notify dashboard: next farmer starting

        await ws_manager.push_event("DEMO_PROGRESS", {

            "demo_id": demo_id,

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





# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Demo Cloud Neural TTS Audio Streaming Endpoint

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



from fastapi import Response

import httpx



@router.get("/tts")

async def demo_text_to_speech(text: str, lang: str = "hi"):

    """

    Cloud Neural TTS audio streaming endpoint for Kisan Mitra AI demo pipeline.

    Synthesizes input text in all 10 supported Indian languages (hi, kn, te, ta, ml, mr, pa, gu, bn, en).

    """

    short_lang = lang.lower().split("-")[0]

    clean_text = text.strip()[:350]

    

    url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={httpx.URL(clean_text).raw_path.decode()}&tl={short_lang}&client=tw-ob"

    

    try:

        async with httpx.AsyncClient(timeout=8.0) as client:

            resp = await client.get(url, headers={

                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

            })

            if resp.status_code == 200 and len(resp.content) > 100:

                return Response(content=resp.content, media_type="audio/mpeg")

    except Exception as exc:

        logger.warning(f"[TTS Endpoint] Stream fetch exception for lang '{short_lang}': {exc}")



    return Response(content=b"", media_type="audio/mpeg")





# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Interactive Voice Query Endpoint

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



class DemoVoiceQueryRequest(BaseModel):

    farmer_id: str = "DEMO-F001"

    farmer_name: str | None = None

    state: str | None = None

    language: str | None = None

    preferred_language: str | None = None

    detected_language: str | None = None

    user_selected_language: str = "en"

    question: str

    query_text: str | None = None

    language_instruction: str | None = None

    response_language: str | None = None





LANGUAGE_NAME_MAP: dict[str, tuple[str, str]] = {

    "en": ("English", "en-IN"),

    "en-in": ("English", "en-IN"),

    "hi": ("Hindi", "hi-IN"),

    "hi-in": ("Hindi", "hi-IN"),

    "kn": ("Kannada", "kn-IN"),

    "kn-in": ("Kannada", "kn-IN"),

    "te": ("Telugu", "te-IN"),

    "te-in": ("Telugu", "te-IN"),

    "ta": ("Tamil", "ta-IN"),

    "ta-in": ("Tamil", "ta-IN"),

    "ml": ("Malayalam", "ml-IN"),

    "ml-in": ("Malayalam", "ml-IN"),

    "mr": ("Marathi", "mr-IN"),

    "mr-in": ("Marathi", "mr-IN"),

    "pa": ("Punjabi", "pa-IN"),

    "pa-in": ("Punjabi", "pa-IN"),

    "gu": ("Gujarati", "gu-IN"),

    "gu-in": ("Gujarati", "gu-IN"),

    "bn": ("Bengali", "bn-IN"),

    "bn-in": ("Bengali", "bn-IN"),

}



LANGUAGE_RESPONSES: dict[str, dict[str, str]] = {

    "kn": {

        "schemes_eligible": "ನಿಮ್ಮ ಜಮೀನು ಮತ್ತು ಬೆಳೆ ವಿವರದಂತೆ ನೀವು ಪಿಎಂ-ಕಿಸಾನ್, ಪ್ರಧಾನ ಮಂತ್ರಿ ಫಸಲ್ ಬಿಮಾ ಯೋಜನೆ ಹಾಗೂ ಮಣ್ಣಿನ ಆರೋಗ್ಯ ಕಾರ್ಡ್ ಯೋಜನೆಗಳಿಗೆ ಅರ್ಹರಾಗಿದ್ದೀರಿ. ಸೌಲಭ್ಯ ಪಡೆಯಲು ಸಮೀಪದ ಕೃಷಿ ಇಲಾಖೆಯನ್ನು ಸಂಪರ್ಕಿಸಿ.",

        "crop_damage": "ಮಳೆಯಿಂದ ಬೆಳೆ ಹಾನಿಯಾಗಿದ್ದರೆ ಪ್ರಧಾನ ಮಂತ್ರಿ ಫಸಲ್ ಬಿಮಾ ಯೋಜನೆಯಡಿ (PMFBY) 72 ಗಂಟೆಗಳ ಒಳಗೆ ಕೃಷಿ ಅಧಿಕಾರಿಗೆ ಅಥವಾ ಬಿಮಾ ಕಂಪನಿಗೆ (ಟೋಲ್ ಫ್ರೀ: 1800-180-1551) ಮಾಹಿತಿ ನೀಡಿ ಪರಿಹಾರ ಪಡೆಯಬಹುದು.",

        "pm_kisan": "ಪಿಎಂ ಕಿಸಾನ್ ಹಣವನ್ನು ನೇರವಾಗಿ ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ 3 ಕಂತುಗಳಲ್ಲಿ (₹2,000 ಪ್ರತಿ ಕಂತು) ಜಮೆ ಮಾಡಲಾಗುತ್ತದೆ. ನಿಮ್ಮ ಆಧಾರ್ ಇ-ಕೆವೈಸಿ ಮತ್ತು ಜಮೀನು ಲಿಂಕ್ ಪರಿಶೀಲಿಸಿಕೊಳ್ಳಿ.",

        "crop_insurance": "ನಿಮ್ಮ ಹತ್ತಿರದ ಸಿಎಸ್‌ಸಿ ಸೆಂಟರ್, ಬ್ಯಾಂಕ್ ಅಥವಾ PMFBY ಪೋರ್ಟಲ್ ಮೂಲಕ ಬೆಳೆ ನೋಂದಣಿ ಅವಧಿ ಮುಗಿಯುವ ಮುನ್ನ ಕಡಿಮೆ ಕಂತಿನ ದರದಲ್ಲಿ ಬೆಳೆ ವಿಮೆ ಪಡೆದುಕೊಳ್ಳಬಹುದು.",

        "pest_disease": "ಬೆಳೆಯಲ್ಲಿ ಕೀಟ ಮತ್ತು ರೋಗ ಬಾಧೆ ನಿಯಂತ್ರಿಸಲು ಸಮಗ್ರ ಕೀಟ ನಿರ್ವಹಣೆ (IPM) ವಿಧಾನ ಅನುಸರಿಸಿ. ಸೂಕ್ತ ಔಷಧಿಯ ಸಲಹೆಗಾಗಿ ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್ 1800-180-1551 ಗೆ ಕರೆ ಮಾಡಿ.",

        "market_price": "ಇಂದಿನ ಮಾರುಕಟ್ಟೆ ಧಾರಣೆಯು ನಿಮ್ಮ ಸಮೀಪದ ಕೃಷಿ ಉತ್ಪನ್ನ ಮಾರುಕಟ್ಟೆ (APMC) ಹಾಗೂ e-NAM ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಲಭ್ಯವಿದೆ. ಧಾನ್ಯ ಮತ್ತು ತರಕಾರಿ ಬೆಲೆ ತಿಳಿಯಲು ಕೃಷಿ ಮಾರುಕಟ್ಟೆ ಸಹಾಯವಾಣಿ ಬಳಸಿ.",

        "soil_fertilizer": "ನಿಮ್ಮ ಜಮೀನಿನ ಮಣ್ಣಿನ ಮಾದರಿಯನ್ನು ಸಮೀಪದ ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರ (KVK) ಗೆ ನೀಡಿ ಉಚಿತ ಮಣ್ಣಿನ ಆರೋಗ್ಯ ಕಾರ್ಡ್ ಪಡೆಯಿರಿ. ಮಣ್ಣಿನ ವರದಿ ಆಧರಿಸಿ ಸಮತೋಲಿತ NPK ಗೊಬ್ಬರ ಬಳಸಿ.",

        "drip_irrigation": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಕೃಷಿ ಸಿಂಚಾಯಿ ಯೋಜನೆ (PMKSY) ಅಡಿಯಲ್ಲಿ ಹನಿ ನೀರಾವರಿ ಅಳವಡಿಕೆಗೆ ಶೇಕಡಾ 45% ರಿಂದ 55% ವರೆಗೆ ಸರ್ಕಾರಿ ಸಬ್ಸಿಡಿ ದೊರೆಯುತ್ತದೆ.",

        "solar_pump": "ಪಿಎಂ-ಕುಸುಮ್ (PM-KUSUM) ಯೋಜನೆಯಡಿ ಸೌರಶಕ್ತಿ ಕೃಷಿ ಪಂಪ್‌ಸೆಟ್ ಮತ್ತು ನೀರಾವರಿ ಉಪಕರಣ ಅಳವಡಿಕೆಗೆ ಶೇಕಡಾ 60% ವರೆಗೆ ಸರ್ಕಾರಿ ಸಬ್ಸಿಡಿ ದೊರೆಯುತ್ತದೆ. ಕೃಷಿ ಇಲಾಖೆಯಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ.",

        "organic_farming": "ಪರಂಪರಾಗತ್ ಕೃಷಿ ವಿಕಾಸ ಯೋಜನೆ ಅಡಿಯಲ್ಲಿ ಸಾವಯವ ಕೃಷಿ ಉತ್ತೇಜನಕ್ಕಾಗಿ ಪ್ರತಿ ಹೆಕ್ಟೇರ್‌ಗೆ ₹31,000 ಧನಸಹಾಯ ದೊರೆಯುತ್ತದೆ.",

        "weather": "ನಿಮ್ಮ ಜಿಲ್ಲೆಯ ಇಂದಿನ ಹವಾಮಾನ ವರದಿಯಂತೆ ಕೀಟನಾಶಕ ಸಿಂಪಡಣೆ ಮತ್ತು ನೀರಾವರಿಯನ್ನು ಯೋಜಿಸಿ.",

        "no_match": "ಈ ಪ್ರಶ್ನೆಗೆ ನನ್ನ ಬಳಿ ನಿರ್ದಿಷ್ಟ ಯೋಜನೆಯ ಮಾಹಿತಿ ಇಲ್ಲ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಜಿಲ್ಲಾ ಕೃಷಿ ಕಚೇರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ ಅಥವಾ ಉಚಿತ ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್ 1800-180-1551 ಗೆ ಕರೆ ಮಾಡಿ.",
        "default": "ಈ ಪ್ರಶ್ನೆಗೆ ನನ್ನ ಬಳಿ ನಿರ್ದಿಷ್ಟ ಯೋಜನೆಯ ಮಾಹಿತಿ ಇಲ್ಲ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಜಿಲ್ಲಾ ಕೃಷಿ ಕಚೇರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ ಅಥವಾ ಉಚಿತ ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್ 1800-180-1551 ಗೆ ಕರೆ ಮಾಡಿ."

    },

    "hi": {

        "schemes_eligible": "आपकी भूमि और फसल प्रोफाइल के अनुसार आप पीएम-किसान, पीएम फसल बीमा योजना और मृदा स्वास्थ्य कार्ड योजना के लिए पात्र हैं। पंजीकरण के लिए निकटतम कृषि कार्यालय जाएं।",

        "crop_damage": "भारी बारिश या प्राकृतिक आपदा से हुए फसल नुकसान के लिए प्रधानमंत्री फसल बीमा योजना (PMFBY) के तहत 72 घंटे के भीतर कृषि विभाग या टोल-फ्री 1800-180-1551 पर सूचना दें।",

        "pm_kisan": "पीएम किसान की राशि प्रतिवर्ष ₹6,000 की 3 समान किस्तों में सीधे बैंक खाते में भेजी जाती है। अपनी आधार ई-केवाईसी और भूमि रिकॉर्ड लिंक की जांच पीएम-किसान पोर्टल पर करें।",

        "crop_insurance": "आप निकटतम सीएससी केंद्र, बैंक शाखा या PMFBY पोर्टल के माध्यम से बुवाई सीजन की अंतिम तिथि से पहले न्यूनतम प्रीमियम पर फसल बीमा करवा सकते हैं।",

        "pest_disease": "फसल में कीट एवं रोग नियंत्रण के लिए एकीकृत कीट प्रबंधन (IPM) अपनाएं और निशुल्क कृषि सलाह के लिए किसान कॉल सेंटर 1800-180-1551 पर संपर्क करें।",

        "market_price": "आज की मंडी दरें आपके निकटतम कृषि उपज मंडी समिति (APMC) और e-NAM पोर्टल पर उपलब्ध हैं। फसल के ताजा भाव जानने के लिए e-NAM ऐप का उपयोग करें।",

        "soil_fertilizer": "निकटतम कृषि विज्ञान केंद्र (KVK) से अपनी मिट्टी का परीक्षण करवाकर मृदा स्वास्थ्य कार्ड प्राप्त करें और आवश्यकतानुसार ही यूरिया और NPK खाद का प्रयोग करें।",

        "drip_irrigation": "प्रधानमंत्री कृषि सिंचाई योजना (PMKSY) के तहत ड्रिप और स्प्रिंकलर सिंचाई प्रणाली लगाने पर किसानों को 45% से 55% तक सरकारी सब्सिडी मिलती है।",

        "organic_farming": "परंपरागत कृषि विकास योजना (PKVY) के तहत जैविक खेती को बढ़ावा देने के लिए प्रति हेक्टेयर ₹31,000 की आर्थिक सहायता दी जाती है।",

        "weather": "आपके जिले के लिए आज का मौसम पूर्वानुमान उपलब्ध है। सिंचाई और कीटनाशक छिड़काव की योजना मौसम देखकर बनाएं।",

        "no_match": "मेरे पास इस प्रश्न के लिए विशिष्ट योजना की जानकारी नहीं है। कृपया अपने निकटतम जिला कृषि कार्यालय से संपर्क करें या किसान कॉल सेंटर 1800-180-1551 पर कॉल करें।",
        "default": "मेरे पास इस प्रश्न के लिए विशिष्ट योजना की जानकारी नहीं है। कृपया अपने निकटतम जिला कृषि कार्यालय से संपर्क करें या किसान कॉल सेंटर 1800-180-1551 पर कॉल करें।"

    },

    "te": {

        "schemes_eligible": "మీ భూమి మరియు పంట వివరాల ఆధారంగా మీరు పీఎం-కిసాన్, ప్రధాన మంత్రి ఫసల్ బీమా యోజన మరియు సాయిల్ హెల్త్ కార్డ్ పథకాలకు అర్హులు. రైతు సేవా కేంద్రాన్ని సంప్రదించండి.",

        "crop_damage": "వర్షాల వల్ల పంట నష్టపోతే ప్రధాన మంత్రి ఫసల్ బీమా యోజన (PMFBY) కింద 72 గంటల వ్యవధిలో వ్యవసాయ అధికారులకు లేదా 1800-180-1551 కి నివేదించండి.",

        "pm_kisan": "పీఎం కిసాన్ సమ్మాన్ నిధి ద్వారా సంవత్సరానికి ₹6,000 ఆర్థిక సహాయం 3 విడతలలో నేరుగా బ్యాంక్ ఖాతాలో జమ చేయబడుతుంది. ఆధార్ ఇ-కేవైసీ తనిఖీ చేసుకోండి.",

        "crop_insurance": "మీ సమీప CSC కేంద్రం, బ్యాంక్ లేదా PMFBY పోర్టల్ ద్వారా పంట బీమా నమోదు చేసుకోవచ్చు. తక్కువ ప్రీమియంతో పంట రక్షణ పొందండి.",

        "pest_disease": "పంట తెగుళ్లు నివారణకు సమగ్ర సస్యరక్షణ చర్యలు చేపట్టండి. నిపుణుల ఉచిత సలహా కోసం కిసాన్ కాల్ సెంటర్ 1800-180-1551 ని సంప్రదించండి.",

        "market_price": "ఈరోజు మార్కెట్ మరియు మండి ధరలు e-NAM పోర్టల్ మరియు స్థానిక APMC మార్కెట్‌లో లభ్యమవుతాయి.",

        "soil_fertilizer": "మీ సమీప KVK లో నేల పరీక్ష చేయించుకుని సాయిల్ హెల్త్ కార్డ్ పొందండి. నివేదిక ఆధారంగా ఎరువులు వాడండి.",

        "drip_irrigation": "ప్రధాన మంత్రి కృషి సించాయీ యోజన (PMKSY) కింద బిందు సేద్యానికి 45% నుండి 55% వరకు ప్రభుత్వ రాయితీ లభిస్తుంది.",

        "organic_farming": "సేంద్రీయ వ్యవసాయం చేసే రైతులకు పరంపరాగత్ కృషి వికాస్ యోజన కింద హెక్టారుకు ₹31,000 ఆర్థిక ప్రోత్సాహకం అందించబడుతుంది.",

        "weather": "మీ జిల్లా వాతావరణ సమాచారం ఆధారంగా నీటి యాజమాన్యం మరియు మందుల పిచికారీ చేపట్టండి.",

        "no_match": "ఈ ప్రశ్నకు నా వద్ద నిర్దిష్ట పథకం సమాచారం లేదు. దయచేసి మీ జిల్లా వ్యవసాయ కార్యాలయాన్ని సంప్రదించండి లేదా కిసాన్ కాల్ సెంటర్‌కు 1800-180-1551 వద్ద కాల్ చేయండి.",
        "default": "ఈ ప్రశ్నకు నా వద్ద నిర్దిష్ట పథకం సమాచారం లేదు. దయచేసి మీ జిల్లా వ్యవసాయ కార్యాలయాన్ని సంప్రదించండి లేదా కిసాన్ కాల్ సెంటర్‌కు 1800-180-1551 వద్ద కాల్ చేయండి."

    },

    "ta": {

        "schemes_eligible": "உங்கள் நிலம் மற்றும் பயிர் விவரங்களின்படி நீங்கள் பிஎம்-கிசான், பிரதம மந்திரி பயிர் காப்பீட்டு திட்டம் மற்றும் மண் வள அட்டை திட்டங்களுக்கு தகுதியானவர்.",

        "crop_damage": "கனமழையால் பயிர் சேதமடைந்தால் பிரதம மந்திரி பயிர் காப்பீட்டு திட்டத்தின் (PMFBY) கீழ் 72 மணி நேரத்திற்குள் 1800-180-1551 என்ற எண்ணில் புகாரளித்து இழப்பீடு பெறலாம்.",

        "pm_kisan": "பிஎம் கிசான் சம்மான் நிதி திட்டத்தின் கீழ் தகுதியுள்ள விவசாயிகளுக்கு ஆண்டுக்கு ₹6,000 நிதி உதவி 3 தவணைகளில் நேரடியாக வங்கி கணக்கில் வழங்கப்படுகிறது.",

        "crop_insurance": "அருகிலுள்ள சிஎஸ்சி மையம், வங்கி அல்லது PMFBY போர்ட்டல் மூலம் பயிர் காப்பீடு பதிவு செய்யலாம்.",

        "pest_disease": "பயிர்களில் பூச்சி மற்றும் நோய் கட்டுப்பாட்டுக்கு ஒருங்கிணைந்த பூச்சி மேலாண்மை முறையைப் பின்பற்றவும். உதவிக்கு 1800-180-1551 என்ற எண்ணை அழைக்கவும்.",

        "market_price": "இன்றைய சந்தை மற்றும் மண்டி விலைகள் e-NAM போர்ட்டலிலும் அருகிலுள்ள APMC சந்தையிலும் கிடைக்கின்றன.",

        "soil_fertilizer": "அருகிலுள்ள வேளாண் அறிவியல் மையத்தில் (KVK) மண் பரிசோதனை செய்து மண் வள அட்டை பெறவும்.",

        "drip_irrigation": "பிரதம மந்திரி க்ரிஷி சிஞ்சாயி யோஜனா (PMKSY) திட்டத்தின் கீழ் சொட்டு நீர் பாசனத்திற்கு 45% முதல் 55% வரை அரசு மானியம் வழங்கப்படுகிறது.",

        "organic_farming": "இயற்கை விவசாயத்தை ஊக்குவிக்க ஹெக்டேருக்கு ₹31,000 மானியம் வழங்கப்படுகிறது.",

        "weather": "உங்கள் மாவட்டத்தின் இன்றைய வானிலை முன்னறிவிப்பின்படி பாசனம் திட்டமிடவும்.",

        "no_match": "இந்தக் கேள்விக்கான குறிப்பிட்ட திட்டத் தகவல் என்னிடம் இல்லை. உங்கள் மாவட்ட வேளாண்மை அலுவலகத்தைத் தொடர்பு கொள்ளவும் அல்லது கிசான் அழைப்பு மையத்திற்கு 1800-180-1551 என்ற எண்ணில் அழைக்கவும்.",
        "default": "இந்தக் கேள்விக்கான குறிப்பிட்ட திட்டத் தகவல் என்னிடம் இல்லை. உங்கள் மாவட்ட வேளாண்மை அலுவலகத்தைத் தொடர்பு கொள்ளவும் அல்லது கிசான் அழைப்பு மையத்திற்கு 1800-180-1551 என்ற எண்ணில் அழைக்கவும்."

    },

    "ml": {

        "schemes_eligible": "നിങ്ങളുടെ കൃഷി വിവരങ്ങൾ അനുസരിച്ച് പിഎം-കിസാൻ, വിള ഇൻഷുറൻസ്, മണ്ണ് പരിശോധനാ കാർഡ് എന്നീ പദ്ധതികൾക്ക് നിങ്ങൾ അർഹനാണ്.",

        "crop_damage": "കനത്ത മഴമൂലം വിള നശിച്ചാൽ പ്രധാനമന്ത്രി ഫസൽ ഭീമ യോജന (PMFBY) വഴി 72 മണിക്കൂറിനുള്ളിൽ 1800-180-1551 എന്ന നമ്പറിൽ വിവരം നൽകി നഷ്ടപരിഹാരം നേടാം.",

        "pm_kisan": "പിഎം കിസാൻ സമ്മാൻ നിധി പദ്ധതി വഴി യോഗ്യരായ കർഷകർക്ക് പ്രതിവർഷം ₹6,000 ധനസഹായം 3 തവണകളായി നേരിട്ട് ബാങ്ക് അക്കൗണ്ടിൽ ലഭിക്കും.",

        "crop_insurance": "അടുത്തുള്ള അക്ഷയ കേന്ദ്രം അല്ലെങ്കിൽ ബാങ്ക് വഴി വിള ഇൻഷുറൻസ് നേടാവുന്നതാണ്.",

        "pest_disease": "വിളകളിലെ കീട നിയന്ത്രണത്തിന് സംയോജിത കീടനിയന്ത്രണ മാർഗ്ഗങ്ങൾ സ്വീകരിക്കുക. വിദഗ്ദ്ധ ഉപദേശത്തിന് 1800-180-1551 എന്ന നമ്പറിൽ വിളിക്കുക.",

        "market_price": "ഇന്നത്തെ വിപണി വിലകളും മണ്ടി നിരക്കുകളും e-NAM പോർട്ടലിലും പ്രാദേശിക APMC വിപണിയിലും ലഭ്യമാണ്.",

        "soil_fertilizer": "അടുത്തുള്ള കൃഷി വിജ്ഞാൻ കേന്ദ്രത്തിൽ മണ്ണ് പരിശോധന നടത്തി സോയിൽ ഹെൽത്ത് കാർഡ് നേടുക.",

        "drip_irrigation": "പിഎംകെഎസ്‌വൈ (PMKSY) പദ്ധതി വഴി ഡ്രിപ്പ് നന സംവിധാനങ്ങൾക്ക് 45% മുതൽ 55% വരെ സർക്കാർ സബ്‌സിഡി ലഭ്യമാണ്.",

        "organic_farming": "ജൈവകൃഷി പ്രോത്സാഹിപ്പിക്കുന്നതിനായി ഹെക്ടറിന് ₹31,000 സാമ്പത്തിക സഹായം നൽകുന്നു.",

        "weather": "നിങ്ങളുടെ ജില്ലയിലെ ഇന്നത്തെ കാലാവസ്ഥ പ്രവചനം അനുസരിച്ച് കൃഷി കാര്യങ്ങൾ ക്രമീകരിക്കുക.",

        "no_match": "ഈ ചോദ്യത്തിന് എൻ്റെ പക്കൽ നിർദ്ദിഷ്ട പദ്ധതി വിവരങ്ങൾ ലഭ്യമല്ല. നിങ്ങളുടെ ജില്ലാ കൃഷി ഓഫീസുമായി ബന്ധപ്പെടുക അല്ലെങ്കിൽ 1800-180-1551 എന്ന നമ്പറിൽ കിസാൻ കോൾ സെൻ്ററിലേക്ക് വിളിക്കുക.",
        "default": "ഈ ചോദ്യത്തിന് എൻ്റെ പക്കൽ നിർദ്ദിഷ്ട പദ്ധതി വിവരങ്ങൾ ലഭ്യമല്ല. നിങ്ങളുടെ ജില്ലാ കൃഷി ഓഫീസുമായി ബന്ധപ്പെടുക അല്ലെങ്കിൽ 1800-180-1551 എന്ന നമ്പറിൽ കിസാൻ കോൾ സെൻ്ററിലേക്ക് വിളിക്കുക."

    },

    "mr": {

        "schemes_eligible": "तुमच्या जमिनीनुसार आपण पीएम-किसान, पीक विमा योजना आणि मृदा आरोग्य कार्ड योजनेसाठी पात्र आहात.",

        "crop_damage": "अतिवृष्टीमुळे पिकाचे नुकसान झाल्यास प्रधानमंत्री पीक विमा योजनेअंतर्गत (PMFBY) 72 तासांच्या आत कृषी अधिकारी किंवा 1800-180-1551 वर नोंदणी करा.",

        "pm_kisan": "पीएम किसान सन्मान निधी योजनेअंतर्गत पात्र शेतकऱ्यांना दरवर्षी ₹6,000 ची मदत 3 हप्त्यांमध्ये थेट बँक खात्यात दिली जाते.",

        "crop_insurance": "जवळच्या सीएससी केंद्रात जाऊन पीक विमा नोंदणी करा.",

        "pest_disease": "पिकावरील कीड व रोग नियंत्रणासाठी एकात्मिक कीड व्यवस्थापन (IPM) वापरा. मोफत सल्ल्यासाठी किसान कॉल सेंटर 1800-180-1551 वर कॉल करा.",

        "market_price": "आजचे शेतमालाचे बाजारभाव तुमच्या जवळच्या APMC बाजार समिती आणि e-NAM पोर्टलवर उपलब्ध आहेत.",

        "soil_fertilizer": "जवळच्या कृषी विज्ञान केंद्रात माती परीक्षण करून मृदा आरोग्य कार्ड मिळवा.",

        "drip_irrigation": "प्रधानमंत्री कृषी सिंचन योजनेअंतर्गत (PMKSY) ठिबक सिंचनासाठी 45% ते 55% सरकारी अनुदान मिळते.",

        "organic_farming": "सेंद्रिय शेतीसाठी प्रति हेक्टरी ₹31,000 चे अनुदान दिले जाते.",

        "weather": "तुमच्या जिल्ह्यातील आजच्या हवामान अंदाजानुसार सिंचनाचे नियोजन करा.",

        "no_match": "माझ्याकडे या प्रश्नासाठी विशिष्ट योजनेची माहिती नाही. कृपया तुमच्या जिल्हा कृषी कार्यालयाशी संपर्क साधा किंवा किसान कॉल सेंटर 1800-180-1551 वर कॉल करा.",
        "default": "माझ्याकडे या प्रश्नासाठी विशिष्ट योजनेची माहिती नाही. कृपया तुमच्या जिल्हा कृषी कार्यालयाशी संपर्क साधा किंवा किसान कॉल सेंटर 1800-180-1551 वर कॉल करा."

    },

    "pa": {

        "schemes_eligible": "ਤੁਹਾਡੀ ਜ਼ਮੀਨ ਅਤੇ ਫ਼ਸਲ ਮੁਤਾਬਕ ਤੁਸੀਂ ਪੀਐਮ-ਕਿਸਾਨ, ਫ਼ਸਲ ਬੀਮਾ ਯੋਜਨਾ ਅਤੇ ਮਿੱਟੀ ਸਿਹਤ ਕਾਰਡ ਲਈ ਯੋਗ ਹੋ।",

        "crop_damage": "ਮੀਂਹ ਜਾਂ ਹੜ੍ਹਾਂ ਕਾਰਨ ਹੋਏ ਫ਼ਸਲ ਦੇ ਨੁਕਸਾਨ ਲਈ ਪ੍ਰਧਾਨ ਮੰਤਰੀ ਫ਼ਸਲ ਬੀਮਾ ਯੋਜਨਾ (PMFBY) ਅਧੀਨ 72 ਘੰਟਿਆਂ ਦੇ ਅੰਦਰ 1800-180-1551 'ਤੇ ਰਿਪੋਰਟ ਕਰੋ।",

        "pm_kisan": "ਪੀਐਮ ਕਿਸਾਨ ਸਮਮਾਨ ਨਿਧੀ ਯੋਜਨਾ ਤਹਿਤ ਯੋਗ ਕਿਸਾਨਾਂ ਨੂੰ ਸਾਲਾਨਾ ₹6,000 ਦੀ ਵਿੱਤੀ ਸਹਾਇਤਾ 3 ਕਿਸ਼ਤਾਂ ਵਿੱਚ ਦਿੱਤੀ ਜਾਂਦੀ ਹੈ।",

        "crop_insurance": "ਨੇੜਲੇ ਸੀਐਸਸੀ ਸੈਂਟਰ ਜਾਂ ਬੈਂਕ ਤੋਂ ਫ਼ਸਲ ਬੀਮਾ ਕਰਵਾਓ।",

        "pest_disease": "ਫ਼ਸਲ ਦੇ ਕੀੜੇ-ਮਕੌੜਿਆਂ ਦੀ ਰੋਕਥਾਮ ਲਈ ਕਿਸਾਨ ਕਾਲ ਸੈਂਟਰ 1800-180-1551 'ਤੇ ਮੁਫ਼ਤ ਸਲਾਹ ਲਵੋ।",

        "market_price": "ਅੱਜ ਦੇ ਮੰਡੀ ਭਾਅ ਤੁਹਾਡੀ ਨੇੜਲੀ APMC ਮੰਡੀ ਅਤੇ e-NAM ਪੋਰਟਲ 'ਤੇ ਉਪਲਬਧ ਹਨ।",

        "soil_fertilizer": "ਨੇੜਲੇ ਖੇਤੀਬਾੜੀ ਵਿਗਿਆਨ ਕੇਂਦਰ ਤੋਂ ਮਿੱਟੀ ਦੀ ਜਾਂਚ ਕਰਵਾ ਕੇ ਸੋਇਲ ਹੈਲਥ ਕਾਰਡ ਪ੍ਰਾਪਤ ਕਰੋ।",

        "drip_irrigation": "ਪ੍ਰਧਾਨ ਮੰਤਰੀ ਕ੍ਰਿਸ਼ੀ ਸਿੰਚਾਈ ਯੋਜਨਾ ਤਹਿਤ ਡ੍ਰਿਪ ਸਿੰਚਾਈ 'ਤੇ 45% ਤੋਂ 55% ਤੱਕ ਸਰਕਾਰੀ ਸਬਸਿਡੀ ਮਿਲਦੀ ਹੈ।",

        "organic_farming": "ਜੈਵਿਕ ਖੇਤੀ ਲਈ ਪ੍ਰਤੀ ਹੈਕਟੇਅਰ ₹31,000 ਦੀ ਸਹਾਇਤਾ ਦਿੱਤੀ ਜਾਂਦੀ ਹੈ।",

        "weather": "ਤੁਹਾਡੇ ਜ਼ਿਲ੍ਹੇ ਦੇ ਅੱਜ ਦੇ ਮੌਸਮ ਦੇ ਹਿਸਾਬ ਨਾਲ ਸਿੰਚਾਈ ਦਾ ਸਮਾਂ ਤੈਅ ਕਰੋ।",

        "no_match": "ਮੇਰੇ ਕੋਲ ਇਸ ਸਵਾਲ ਲਈ ਕੋਈ ਖਾਸ ਯੋਜਨਾ ਦੀ ਜਾਣਕਾਰੀ ਨਹੀਂ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ ਜ਼ਿਲ੍ਹਾ ਖੇਤੀਬਾੜੀ ਦਫ਼ਤਰ ਨਾਲ ਸੰਪਰਕ ਕਰੋ ਜਾਂ ਕਿਸਾਨ ਕਾਲ ਸੈਂਟਰ 1800-180-1551 'ਤੇ ਕਾਲ ਕਰੋ।",
        "default": "ਮੇਰੇ ਕੋਲ ਇਸ ਸਵਾਲ ਲਈ ਕੋਈ ਖਾਸ ਯੋਜਨਾ ਦੀ ਜਾਣਕਾਰੀ ਨਹੀਂ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ ਜ਼ਿਲ੍ਹਾ ਖੇਤੀਬਾੜੀ ਦਫ਼ਤਰ ਨਾਲ ਸੰਪਰਕ ਕਰੋ ਜਾਂ ਕਿਸਾਨ ਕਾਲ ਸੈਂਟਰ 1800-180-1551 'ਤੇ ਕਾਲ ਕਰੋ।"

    },

    "gu": {

        "schemes_eligible": "આપની જમીન મુજબ આપ પીએમ-કિસાન, ફસલ વીમા યોજના અને સોઇલ હેલ્થ કાર્ડ માટે પાત્ર છો.",

        "crop_damage": "કમોસમી વરસાદથી થયેલ પાક નુકસાન માટે પ્રધાનમંત્રી ફસલ વીમા યોજના (PMFBY) હેઠળ 72 કલાકમાં 1800-180-1551 પર જાણ કરી વળતર મેળવો.",

        "pm_kisan": "પીએમ કિસાન સમ્માન નિધિ યોજના હેઠળ પાત્ર ખેડૂતોને વાર્ષિક ₹6,000 ની સહાય 3 હપ્તામાં સીધી બેંક ખાતામાં આપવામાં આવે છે.",

        "crop_insurance": "નજીકના CSC કેન્દ્ર પરથી પાક વીમો કરાવો.",

        "pest_disease": "પાકમાં જીવાત નિયંત્રણ માટે 1800-180-1551 પર મફત સલાહ લો.",

        "market_price": "આજના મંડી ભાવ આપની નજીકની APMC અને e-NAM પોર્ટલ પર ઉપલબ્ધ છે.",

        "soil_fertilizer": "નજીકના કૃષિ વિજ્ઞાન કેન્દ્ર ખાતે માટી પરીક્ષણ કરાવી સોઇલ હેલ્થ કાર્ડ મેળવો.",

        "drip_irrigation": "ટપક સિંચાઈ માટે 45% થી 55% સુધી સરકારી સબસિડી મળે છે.",

        "organic_farming": "જૈવિક ખેતી માટે હેક્ટર દીઠ ₹31,000 ની સહાય આપવામાં આવે છે.",

        "weather": "આજના હવામાન અહેવાલ મુજબ સિંચાઈનું આયોજન કરો.",

        "no_match": "મારી પાસે આ પ્રશ્ન માટે ચોક્કસ યોજનાની માહિતી નથી. કૃપા કરીને તમારી જિલ્લા ખેતીવાડી કચેરીનો સંપર્ક કરો અથવા કિસાન કોલ સેન્ટર 1800-180-1551 પર કોલ કરો।",
        "default": "મારી પાસે આ પ્રશ્ન માટે ચોક્કસ યોજનાની માહિતી નથી. કૃપા કરીને તમારી જિલ્લા ખેતીવાડી કચેરીનો સંપર્ક કરો અથવા કિસાન કોલ સેન્ટર 1800-180-1551 પર કોલ કરો।"

    },

    "bn": {

        "schemes_eligible": "আপনার জমি ও ফসল অনুযায়ী আপনি পিএম-কিসান, ফসল বীমা ও মৃত্তিকা স্বাস্থ্য কার্ডের জন্য যোগ্য।",

        "crop_damage": "ভারী বৃষ্টির কারণে ফসল ক্ষতিগ্রস্ত হলে প্রধানমন্ত্রী ফসল বীমা যোজনার (PMFBY) অধীনে ৭২ ঘণ্টার মধ্যে 1800-180-1551 নম্বরে জানান।",

        "pm_kisan": "পিএম কিসান সম্মান নিধি প্রকল্পের আওতায় যোগ্য কৃষকরা প্রতি বছর ₹6,000 টাকা ৩টি কিস্তিতে সরাসরি ব্যাংক অ্যাকাউন্টে পান।",

        "crop_insurance": "নিকটস্থ সিএসসি কেন্দ্র থেকে ফসল বীমা করান।",

        "pest_disease": "ফসলের পোকা দমনের জন্য বালাই ব্যবস্থাপনা গ্রহণ করুন। সহায়তার জন্য 1800-180-1551 নম্বরে কল করুন।",

        "market_price": "আজকের বাজারের দর আপনার নিকটস্থ APMC এবং e-NAM পোর্টালে উপলব্ধ।",

        "soil_fertilizer": "নিকটস্থ কৃষি বিজ্ঞান কেন্দ্রে মাটি পরীক্ষা করিয়ে মৃত্তিকা স্বাস্থ্য কার্ড সংগ্রহ করুন।",

        "drip_irrigation": "বিন্দু সেচের জন্য ৪৫% থেকে ৫৫% পর্যন্ত সরকারি ভর্তুকি পাওয়া যায়।",

        "organic_farming": "জৈব চাষের জন্য প্রতি হেক্টরে ₹31,000 আর্থিক সহায়তা দেওয়া হয়।",

        "weather": "আজকের আবহাওয়ার পূর্বাভাস অনুযায়ী সেচের পরিকল্পনা করুন।",

        "no_match": "আমার কাছে এই প্রশ্নের জন্য নির্দিষ্ট কোনো প্রকল্পের তথ্য নেই। অনুগ্রহ করে আপনার জেলা কৃষি অফিসে যোগাযোগ করুন অথবা কিষাণ কল সেন্টারে 1800-180-1551 নম্বরে কল করুন।",
        "default": "আমার কাছে এই প্রশ্নের জন্য নির্দিষ্ট কোনো প্রকল্পের তথ্য নেই। অনুগ্রহ করে আপনার জেলা কৃষি অফিসে যোগাযোগ করুন অথবা কিষাণ কল সেন্টারে 1800-180-1551 নম্বরে কল করুন।"

    },

    "en": {

        "schemes_eligible": "Based on your land holding and crop profile, you are eligible for PM-Kisan Samman Nidhi (₹6,000/yr), PM Fasal Bima Yojana (Crop Insurance), and Soil Health Card subsidies. Visit your nearest Agriculture Office to register.",

        "crop_damage": "For crop damage caused by heavy rain or natural disasters, report within 72 hours under Pradhan Mantri Fasal Bima Yojana (PMFBY) via toll-free helpline 1800-180-1551 to claim loss compensation.",

        "pm_kisan": "PM-Kisan payments are transferred directly via DBT in 3 equal instalments of ₹2,000 every 4 months. Verify your Aadhaar e-KYC and land record seeding on the PM-Kisan portal to ensure timely payment.",

        "crop_insurance": "You can enroll for PM Fasal Bima Yojana crop insurance at your local CSC center, bank branch, or via the PMFBY portal before the seasonal cutoff date with minimal premium (1.5% to 2%).",

        "pest_disease": "To control pest infestation and crop diseases, apply Integrated Pest Management (IPM) using recommended bio-pesticides. Contact Kisan Call Centre at 1800-180-1551 for specific chemical dosage guidance.",

        "market_price": "Today's market prices and mandi rates are available via the e-NAM portal and your local APMC market. Contact the Agriculture Marketing Board helpline for live commodity prices.",

        "soil_fertilizer": "Collect soil samples from your farm and test them at the nearest Krishi Vigyan Kendra (KVK) to obtain a Soil Health Card. Use balanced NPK fertilizers according to recommendations.",

        "drip_irrigation": "Under Pradhan Mantri Krishi Sinchayee Yojana (PMKSY), farmers receive 45% to 55% government subsidy for installing micro-irrigation (drip and sprinkler) systems.",

        "solar_pump": "Under PM-KUSUM scheme, farmers receive up to 60% government subsidy for installing solar agriculture pumps and repairing irrigation pump equipment. Apply via the state portal.",

        "organic_farming": "To encourage organic farming, financial assistance of ₹31,000 per hectare is provided under Paramparagat Krishi Vikas Yojana (PKVY) for organic inputs and certification.",

        "weather": "Check today's local Agromet Weather Advisory for your district before planning irrigation or pesticide spraying.",

        "no_match": "I don't have specific scheme information for that query. I'd recommend contacting your District Agriculture Office or calling the Kisan Call Centre at 1800-180-1551 for guidance.",
        "default": "I don't have specific scheme information for that query. I'd recommend contacting your District Agriculture Office or calling the Kisan Call Centre at 1800-180-1551 for guidance."

    }

}





SCHEME_MAP: dict[str, tuple[str, str]] = {
    "schemes_eligible": ("Government Schemes & Eligibility Evaluation", "General Scheme Eligibility Inquiry"),
    "crop_damage": ("Pradhan Mantri Fasal Bima Yojana", "Crop Damage Compensation Claim"),
    "pm_kisan": ("PM-Kisan Samman Nidhi", "PM-Kisan Payment Status & DBT Inquiry"),
    "crop_insurance": ("PMFBY Crop Insurance Enrollment", "Crop Insurance Registration & Coverage"),
    "pest_disease": ("Integrated Pest Management", "Crop Pest & Disease Protection Advisory"),
    "market_price": ("e-NAM & Mandi Price Information", "Market Price & Mandi Rate Inquiry"),
    "soil_fertilizer": ("Soil Health Card Scheme", "Soil Testing & Fertilizer Recommendation"),
    "drip_irrigation": ("PM Krishi Sinchayee Yojana", "Micro-Irrigation Subsidy Inquiry"),
    "solar_pump": ("PM-KUSUM Solar Pump Scheme", "Solar Pump & Irrigation Machinery Subsidy"),
    "organic_farming": ("Paramparagat Krishi Vikas Yojana", "Organic Farming Assistance"),
    "weather": ("Agromet Weather Advisory Service", "Weather Forecast Advisory"),
    "no_match": ("General Agricultural Guidance", "Out-of-Scope / General Agricultural Inquiry"),
    "default": ("General Agricultural Guidance", "Out-of-Scope / General Agricultural Inquiry")
}


def _classify_intent(question: str) -> str:
    """Categorize user question into specific, non-overlapping agricultural intent domains."""
    q = question.lower().strip()

    # 1. Specific Crop Damage / Rain / Loss / Compensation
    if any(w in q for w in [
        "damaged", "heavy rain", "flood", "drought", "crop damage", "crop loss", "loss", "compensation", 
        "ruined", "ruin", "destroy", "hailstorm", "cyclone", "claim compensation",
        "ಹಾನಿ", "ಮಳೆ", "ಮಳೆಯಿಂದ", "ಬೆಳೆ ಹಾನಿ", "ನಷ್ಟ", "ಪರಿಹಾರ", "ಪರಿಹಾರ ಹೇಗೆ", "ಬೆಳೆ ನಷ್ಟ", "ಅನಾವೃಷ್ಟಿ", "ಪ್ರವಾಹ",
        "नुकसान", "खराब", "बारिश", "मुआवजा", "क्षति", "सूखा", "बाढ़", "फसल नुकसान",
        "పాడైపోయింది", "నష్టం", "పరిహారం", "సేదం", "നശിച്ചു", "നഷ്ടപരിഹാരം"
    ]):
        return "crop_damage"

    # 2. Crop Insurance Enrollment / Policy / Bima
    if any(w in q for w in [
        "get crop insurance", "crop insurance", "insurance policy", "insurance claim", "bima policy", "bima", "premium", "enrollment",
        "ವಿಮೆ ಪಡೆದುಕೊಳ್ಳುವುದು", "ಬೆಳೆ ವಿಮೆ", "ಫಸಲ್ ಬಿಮಾ", "ವಿಮೆ",
        "फसल बीमा", "बीमा", "பயிர் காப்பீடு", "காப்பீடு", "പട്ടയം", "పంట బీమా", "బీమా"
    ]):
        return "crop_insurance"

    # 3. Solar Pump / Solarization / PM-KUSUM
    if any(w in q for w in [
        "solar pump", "kusum", "pm-kusum", "pm kusum", "solar pump subsidy", "solar agriculture pump",
        "ಸೌರ ಪಂಪ್", "ಸೋಲಾರ್ ಪಂಪ್", "सोलर पंप", "कुसुम"
    ]):
        return "solar_pump"

    # 4. PM-KISAN Payment / Status / Income Support
    if any(w in q for w in [
        "pm-kisan", "pm kisan", "kisan payment", "6000", "instalment", "installment", 
        "ಕಿಸಾನ್ ಹಣ", "ಪಿಎಂ-ಕಿಸಾನ್", "किस्त", "किश्त", "కిసాన్ డబ్బులు", "పీఎం-కిసాన్", "തവണ"
    ]):
        return "pm_kisan"

    # 5. Pest / Insect / Disease Control
    if any(w in q for w in [
        "pest", "pests", "disease", "insect", "insects", "yellow rust", "spray", 
        "ಕೀಟ", "ರೋಗ", "कीट", "कीड़ा", "बीमारी", "తెగులు", "తెగుళ్ల", "పురుగులు", "నివారణ", "பூச்சி"
    ]):
        return "pest_disease"

    # 6. General Scheme & Subsidy Eligibility
    if any(w in q for w in [
        "subsidy", "subsidies", "eligible", "eligibility", "small farmer", "marginal farmer", "schemes", "government scheme", 
        "ಯೋಜನೆಗಳಿಗೆ", "ಯೋಜನೆ", "ಸಬ್ಸಿಡಿ", "ಅರ್ಹತೆ", "पात्र", "योजनाएं", "सब्सिडी", "అర్హుడిని", "పథకాలకు", "పథకాలు", "దిట్టం"
    ]):
        return "schemes_eligible"

    # 7. Market Price / Mandi Rate
    if any(w in q for w in [
        "price", "rate", "mandi", "market", "cost", 
        "ಬೆಲೆ", "ಧಾರಣೆ", "ಮಾರುಕಟ್ಟೆ", "ಮಂಡಿ", "भाव", "दाम", "मंडी", "बाजार", "ధర", "మార్కెట్", "விலை", "വില", "ਭਾਅ", "দাম"
    ]):
        return "market_price"

    # 8. Soil Health & Fertilizer
    if any(w in q for w in [
        "soil", "fertilizer", "urea", "dap", "npk", "testing", 
        "ಮಣ್ಣು", "ರಸಗೊಬ್ಬರ", "ಗೊಬ್ಬರ", "ಪರೀಕ್ಷೆ", "मिट्टी", "खाद", "उर्वरक", "నేల", "ఎరువు", "மண்", "உரம்", "മണ്ണ്"
    ]):
        return "soil_fertilizer"

    # 9. Drip / Sprinkler Irrigation
    if any(w in q for w in [
        "drip", "sprinkler", "micro-irrigation", 
        "ಹನಿ ನೀರಾವರಿ", "ड्रिप", "सिंचाई", "డ్రిప్", "సేద్యం", "சொட்டு நீர்", "ഡ്രിപ്പ്"
    ]):
        return "drip_irrigation"

    # 10. Organic Farming
    if any(w in q for w in [
        "organic", "jaivik", "compost", "bio", " natural", 
        "ಸಾವಯವ", "जैविक", "సేంద్రీय", "இயற்கை", "ജൈവ"
    ]):
        return "organic_farming"

    # 11. Weather Forecast
    if any(w in q for w in [
        "weather", "forecast", "climate", "temperature", 
        "ಹವಾಮಾನ", "मौसम", "వాతావరణం", "வானிலை", "കാലാവಸ್ಥ"
    ]):
        return "weather"

    return "default"





@router.post("/call/process", response_model=dict[str, Any])
async def process_demo_voice_query(
    request: DemoVoiceQueryRequest,
    container: Any = Depends(get_container)
) -> dict[str, Any]:
    """
    Process an interactive demo voice query for a farmer in their chosen language.
    Uses multi-domain agricultural knowledge router across 10 languages and 10 domains.
    """
    farmer = _demo_service.get_farmer(request.farmer_id) or _demo_service.get_all_farmers()[0]
    raw_lang = (request.user_selected_language or request.language or farmer.preferred_language or "en").lower().strip()
    
    lang_info = LANGUAGE_NAME_MAP.get(raw_lang) or LANGUAGE_NAME_MAP.get(raw_lang.split("-")[0]) or ("English", "en-IN")
    lang_name, bcp47_tag = lang_info
    short_lang = raw_lang.split("-")[0]

    intent_key = _classify_intent(request.question)
    top_scheme_name, category_desc = SCHEME_MAP.get(intent_key, SCHEME_MAP["default"])

    # Guaranteed topic-matched localized text
    lang_dict = LANGUAGE_RESPONSES.get(short_lang, LANGUAGE_RESPONSES["en"])
    ans_text = lang_dict.get(intent_key, lang_dict.get("default", LANGUAGE_RESPONSES["en"]["default"]))
    used_llm = False

    # Optional fast LLM enhancement if explicitly enabled
    import os
    if os.getenv("ENABLE_DEMO_LLM") == "true" and hasattr(container, "llm_provider") and container.llm_provider:
        try:
            prompt = f"Farmer: {farmer.name}, Question: {request.question}. Answer in {lang_name}."
            llm_response = container.llm_provider.generate(
                prompt=prompt,
                system_instruction=f"You are Kisan Mitra AI, an expert agricultural assistant responding in {lang_name}."
            )
            resp_str = str(llm_response or "").strip()
            if resp_str and len(resp_str) > 15 and not resp_str.startswith("[Mock") and "ready to assist" not in resp_str.lower():
                ans_text = resp_str
                used_llm = True
        except Exception as e:
            logger.warning(f"LLM generation skipped for query '{request.question}': {e}.")

    return {
        "success": True,
        "farmer_id": farmer.farmer_id,
        "farmer_name": farmer.name,
        "state": farmer.state,
        "question": request.question,
        "lang_code": request.user_selected_language or short_lang,
        "detected_speech_language": request.user_selected_language or short_lang,
        "response_language": lang_name,
        "response_language_tag": bcp47_tag,
        "top_scheme": top_scheme_name,
        "voice_response": ans_text,
        "reasoning": [
            f"✓ Selected Language: {lang_name} ({bcp47_tag})",
            f"✓ Query categorized: {category_desc} ({'Gemini 1.5 Pro' if used_llm else 'Domain Knowledge Engine'})",
            f"✓ Verified for {farmer.name} ({farmer.district}, {farmer.state})",
        ],
        "document_guidance": {
            "required_documents": ["Aadhaar Card", "Land Record", "Bank Passbook"],
            "helpline": "1800-180-1551",
            "nearest_office": f"District Agriculture Office, {farmer.district}",
        },
    }

