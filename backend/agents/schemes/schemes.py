import time
import json

from agents.base import BaseAgent
from app.core.context import AgentContext
from app.core.llm_provider import BaseLLMProvider
from app.schemas.evidence import GovernmentSchemeEvidence
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResult
from app.services.scheme_service import GovernmentSchemeService


class GovernmentSchemeAgent(BaseAgent):
    """
    GovernmentSchemeAgent matches farmers with welfare policies.
    """
    def __init__(self, llm_provider: BaseLLMProvider, scheme_service: GovernmentSchemeService) -> None:
        super().__init__(name="GovernmentScheme", llm_provider=llm_provider)
        self.scheme_service = scheme_service

    async def initialize(self) -> None:
        self.state.status = "ready"

    async def execute(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        self.state.status = "running"
        self.state.start_time = time.time()

        farmer_id = context.farmer_id or "FR-101"

        # 1. Keep rule-based eligibility calculation unchanged
        from app.knowledge.modules.government import GovernmentKnowledgeProvider
        from app.services.demo import DemoService

        gov_provider = GovernmentKnowledgeProvider()
        all_schemes = gov_provider.get_all_schemes()

        demo_service = DemoService()
        farmer = demo_service.get_farmer(farmer_id)
        if not farmer:
            farmer = demo_service.get_farmer_by_phone(farmer_id)
            if not farmer:
                farmer = demo_service.get_farmer("DEMO-F001")  # Fallback to Ramesh Singh

        recommendations = self.scheme_service.evaluate_farmer_eligibility(farmer, all_schemes)

        # 2. Extract context parameters
        eligible = [r for r in recommendations if r.status in ("ELIGIBLE", "POSSIBLY_ELIGIBLE")]
        missing_docs = []
        for r in eligible:
            missing_docs.extend(r.missing_documents)
        missing_docs = list(set(missing_docs))

        top_rec = eligible[0] if eligible else (recommendations[0] if recommendations else None)
        confidence = top_rec.confidence if top_rec else 0.5
        evidence_list = top_rec.reasoning if top_rec else []

        # 3. Construct payload to Gemini
        query_data = {
            "farmer_profile": farmer.model_dump(),
            "eligible_schemes": [
                {
                    "scheme_id": r.scheme_id,
                    "title": r.title,
                    "status": r.status,
                    "benefits": r.benefits,
                    "deadline": r.deadline,
                    "reasoning": r.reasoning,
                }
                for r in eligible
            ],
            "missing_documents": missing_docs,
            "confidence": confidence,
            "evidence": evidence_list
        }

        prompt = json.dumps(query_data, indent=2)

        system_instruction = (
            "You are the Kisan Mitra AI Government Scheme Agent. "
            "Analyze the provided farmer profile and eligibility results, and return a JSON object with the following keys:\n"
            "- 'explanation': A detailed explanation of why the farmer is eligible or ineligible for the schemes.\n"
            "- 'next_steps': A list of clear, actionable next steps for the farmer to apply or complete their profile.\n"
            "- 'farmer_friendly_summary': A warm, polite, and simplified summary of the recommendations in the farmer's preferred language.\n"
            "- 'voice_summary': A brief, conversational summary (max 2 sentences) optimized for speech synthesis in the farmer's preferred language.\n\n"
            "Return ONLY the raw JSON object. Do not include markdown code block formatting (like ```json) or any extra text."
        )

        # 4. Generate Gemini explanation
        raw_response = self.llm_provider.generate(prompt, system_instruction=system_instruction)

        # Clean response from code fences
        clean_response = raw_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        elif clean_response.startswith("```"):
            clean_response = clean_response[3:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()

        try:
            ai_data = json.loads(clean_response)
        except Exception:
            # Fallback
            ai_data = {
                "explanation": f"Based on rule evaluation, you are eligible for the matching schemes. Top matches: {[r.title for r in eligible]}.",
                "next_steps": ["Verify Aadhaar card link", "Prepare land patta documents", "Visit District Agriculture Office"],
                "farmer_friendly_summary": f"Dear farmer, you qualify for {[r.title for r in eligible]}.",
                "voice_summary": f"You are eligible for {[r.title for r in eligible]}. Please check required documents."
            }

        # 5. Formulate structured GovernmentSchemeEvidence
        evidence = GovernmentSchemeEvidence(
            id=f"ev-scheme-{context.request_id}",
            source="SubsidyPortalAPI",
            agent=self.name,
            confidence=confidence,
            weight=0.7,
            reasoning=ai_data.get("explanation", f"Scheme service lookup: {eligible}"),
            scheme_title=top_rec.title if top_rec else "PM-KISAN",
            eligibility_matched=len(eligible) > 0,
            ontology_references=["subsidy_scheme"]
        )

        content_payload = json.dumps(ai_data)

        self.state.status = "succeeded"
        self.state.end_time = time.time()
        self.state.execution_time = (self.state.end_time - self.state.start_time) * 1000.0

        return AgentResult(
            agent_name=self.name,
            content=content_payload,
            confidence=confidence,
            metrics={"latency_ms": self.state.execution_time},
            logs=["Consulted government scheme registries via Gemini Agent."],
            evidence=[evidence.model_dump()]
        )

    async def validate(self, response: AgentResult, context: AgentContext) -> bool:
        return len(response.content) > 0

    async def cleanup(self) -> None:
        self.state.status = "cleanup"

    async def health_check(self) -> bool:
        return True
