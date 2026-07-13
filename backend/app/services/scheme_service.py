"""
Kisan Mitra AI — Government Scheme Service
=============================================
Domain service coordinating government scheme queries,
eligibility evaluation, and document advisory generation.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.context import AgentContext
from app.models.farmer import Farmer
from app.models.scheme import SchemeRecommendation
from app.services.document_advisor import DocumentAdvisor
from app.services.eligibility import EligibilityEngine
from app.tools.scheme_tool import GovernmentSchemeTool

logger = logging.getLogger("kisan_mitra_ai.services.scheme_service")


class GovernmentSchemeService:
    """
    Domain service encapsulating government subsidy schemes eligibility.
    Coordinates between Knowledge Provider, Eligibility Engine, and Document Advisor.
    """
    def __init__(self) -> None:
        self.scheme_tool = GovernmentSchemeTool()
        self.eligibility_engine = EligibilityEngine()
        self.document_advisor = DocumentAdvisor()

    async def get_schemes_eligibility(self, farmer_id: str, context: AgentContext) -> str:
        """
        Coordinates querying government schemes, incorporating active integration details if configured.
        """
        container = context.metadata.get("container") if context else None
        if container and hasattr(container, "integration_registry"):
            active_adapter = container.integration_registry.get_active("government")
            if active_adapter:
                try:
                    result = await container.resilient_runner.execute(
                        integration_id=active_adapter.metadata.id,
                        operation_name="list_schemes",
                        func=lambda: active_adapter.list_schemes(),
                        trace_id=context.trace_id,
                        request_id=context.request_id,
                        session_id=context.session_id
                    )
                    schemes_text = "; ".join([f"{s.get('name')}: {s.get('benefit')} ({s.get('type')})" for s in result])
                    return (
                        f"Government Integration ({active_adapter.metadata.name}) output: "
                        f"Schemes retrieved: {schemes_text}."
                    )
                except Exception as e:
                    return f"Government Integration ({active_adapter.metadata.name}) failed: {e!s}. Falling back to default eligibility."

        return await self.scheme_tool.run({"farmer_id": farmer_id}, context)

    def evaluate_farmer_eligibility(
        self,
        farmer: Farmer,
        schemes: list[dict[str, Any]],
    ) -> list[SchemeRecommendation]:
        """
        Evaluate a farmer against all available schemes.
        Returns sorted list of SchemeRecommendations.
        """
        from app.schemes.scheme_service import SchemeService
        service = SchemeService()
        return service.get_recommendations(farmer)

    def get_document_guidance(
        self,
        farmer: Farmer,
        recommendation: SchemeRecommendation,
    ) -> dict[str, Any]:
        """Generate document and application guidance for a scheme."""
        return self.document_advisor.generate_guidance(farmer, recommendation)

    def generate_voice_response(
        self,
        farmer: Farmer,
        recommendations: list[SchemeRecommendation],
        language: str = "hi",
    ) -> str:
        """
        Generate a natural, conversational voice response summarizing eligibility.
        """
        name = farmer.name.split()[0]
        eligible = [r for r in recommendations if r.status == "ELIGIBLE"]
        possibly = [r for r in recommendations if r.status == "POSSIBLY_ELIGIBLE"]
        need_info = [r for r in recommendations if r.status == "NEED_MORE_INFO"]

        if not eligible and not possibly:
            return self._no_schemes_response(name, language)

        parts: list[str] = []

        if eligible:
            top = eligible[0]
            if language == "hi":
                parts.append(
                    f"{name} जी, आपकी प्रोफ़ाइल के अनुसार, "
                    f"आप {top.title} के लिए पात्र हैं। "
                    f"इसके तहत {top.benefits} "
                    f"कृपया {', '.join(top.required_documents[:3])} तैयार रखें। "
                    f"आवेदन {top.nearest_office} पर करें।"
                )
                if top.deadline:
                    parts.append(f"अंतिम तिथि: {top.deadline}।")
                if len(eligible) > 1:
                    others = ", ".join(r.title for r in eligible[1:3])
                    parts.append(f"इसके अलावा आप {others} के लिए भी पात्र हैं।")
            elif language == "pa":
                parts.append(
                    f"{name} ਜੀ, ਤੁਹਾਡੀ ਪ੍ਰੋਫਾਈਲ ਅਨੁਸਾਰ, "
                    f"ਤੁਸੀਂ {top.title} ਲਈ ਯੋਗ ਹੋ। "
                    f"ਇਸ ਤਹਿਤ {top.benefits} "
                    f"ਕਿਰਪਾ ਕਰਕੇ {', '.join(top.required_documents[:3])} ਤਿਆਰ ਰੱਖੋ।"
                )
                if top.deadline:
                    parts.append(f"ਆਖ਼ਰੀ ਤਰੀਕ: {top.deadline}।")
            else:
                parts.append(
                    f"Based on your profile {name}, "
                    f"you are eligible for {top.title}. "
                    f"{top.benefits} "
                    f"Please keep {', '.join(top.required_documents[:3])} ready. "
                    f"Apply at {top.nearest_office}."
                )
                if top.deadline:
                    parts.append(f"Deadline: {top.deadline}.")
                if len(eligible) > 1:
                    others = ", ".join(r.title for r in eligible[1:3])
                    parts.append(f"You are also eligible for {others}.")

        if possibly and not eligible:
            top = possibly[0]
            if language == "hi":
                parts.append(f"{name} जी, आप {top.title} के लिए संभावित पात्र हैं। कृपया अधिक जानकारी प्रदान करें।")
            elif language == "pa":
                parts.append(f"{name} ਜੀ, ਤੁਸੀਂ {top.title} ਲਈ ਸੰਭਾਵਿਤ ਯੋਗ ਹੋ। ਕਿਰਪਾ ਕਰਕੇ ਹੋਰ ਜਾਣਕਾਰੀ ਦਿਓ।")
            else:
                parts.append(f"{name}, you may be eligible for {top.title}. Please provide more details for confirmation.")

        # Helpline
        if eligible and eligible[0].helpline:
            if language == "hi":
                parts.append(f"अधिक जानकारी के लिए {eligible[0].helpline} पर कॉल करें।")
            elif language == "pa":
                parts.append(f"ਹੋਰ ਜਾਣਕਾਰੀ ਲਈ {eligible[0].helpline} ਤੇ ਕਾਲ ਕਰੋ।")
            else:
                parts.append(f"For more details, call {eligible[0].helpline}.")

        return " ".join(parts)

    def _no_schemes_response(self, name: str, language: str) -> str:
        if language == "hi":
            return (
                f"{name} जी, वर्तमान में आपकी प्रोफ़ाइल से मिलती-जुलती कोई योजना नहीं मिली। "
                "कृपया अपने ज़िले के कृषि कार्यालय से संपर्क करें या हेल्पलाइन 1800-180-1551 पर कॉल करें।"
            )
        elif language == "pa":
            return (
                f"{name} ਜੀ, ਵਰਤਮਾਨ ਵਿੱਚ ਤੁਹਾਡੀ ਪ੍ਰੋਫਾਈਲ ਨਾਲ ਮੇਲ ਖਾਂਦੀ ਕੋਈ ਯੋਜਨਾ ਨਹੀਂ ਮਿਲੀ। "
                "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ ਜ਼ਿਲ੍ਹੇ ਦੇ ਖੇਤੀ ਦਫ਼ਤਰ ਨਾਲ ਸੰਪਰਕ ਕਰੋ।"
            )
        return (
            f"{name}, no matching schemes were found for your profile currently. "
            "Please contact your district agriculture office or call helpline 1800-180-1551."
        )
