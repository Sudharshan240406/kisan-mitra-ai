"""
Kisan Mitra AI — Government Scheme Tool
==========================================
Queries the Government Schemes Knowledge Base and Eligibility Engine
to produce actionable scheme recommendations for farmers.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.context import AgentContext
from app.core.tool import BaseTool
from app.models.farmer import Farmer
from app.services.eligibility import EligibilityEngine

logger = logging.getLogger("kisan_mitra_ai.tools.scheme_tool")


class GovernmentSchemeTool(BaseTool):
    """
    GovernmentSchemeTool queries the knowledge provider for matching schemes
    and evaluates farmer eligibility using the EligibilityEngine.
    """
    def __init__(self) -> None:
        super().__init__(
            name="GovernmentSchemeTool",
            description="Queries government welfare scheme catalog and evaluates farmer eligibility."
        )
        self._eligibility_engine = EligibilityEngine()

    async def run(self, args: dict[str, Any], context: AgentContext) -> str:
        query = args.get("query", "government schemes farmer eligibility")
        container = context.metadata.get("container") if context else None

        from app.schemes.scheme_service import SchemeService
        service = SchemeService()

        # Build farmer profile
        farmer = self._build_farmer_profile(args, container)

        # Match schemes based on AI query (Task 5)
        matched_schemes = service.route_ai_query(query)
        if not matched_schemes:
            return "GovernmentSchemeTool output: No matching schemes found for this farmer profile."

        # Evaluate matched schemes
        recommendations = []
        for s in matched_schemes:
            status, reason, confidence = service.evaluate_eligibility(farmer, s["id"])
            rec_status = "ELIGIBLE"
            if status == "Possibly Eligible":
                rec_status = "POSSIBLY_ELIGIBLE"
            elif status == "Not Eligible":
                rec_status = "NOT_ELIGIBLE"

            # Filter documents to only return those required
            docs = list(s["required_documents"])

            from app.models.scheme import SchemeRecommendation
            recommendations.append(SchemeRecommendation(
                scheme_id=s["id"],
                title=s["title"],
                status=rec_status,
                confidence=confidence,
                reasoning=[reason],
                benefits=s["benefits"],
                required_documents=docs,
                nearest_office=s["nearest_office"],
                department=s["department"],
                helpline=s["helpline"],
                official_url=s["url"]
            ))

        # Format output
        output_parts = []
        eligible_count = 0
        for rec in recommendations:
            if rec.status == "ELIGIBLE":
                eligible_count += 1
                output_parts.append(
                    f"✓ ELIGIBLE: {rec.title} — {rec.benefits} "
                    f"(Confidence: {rec.confidence*100:.0f}%) "
                    f"Documents: {', '.join(rec.required_documents)}. "
                    f"Deadline: {rec.deadline}. Helpline: {rec.helpline}."
                )
            elif rec.status == "POSSIBLY_ELIGIBLE":
                output_parts.append(
                    f"? POSSIBLY ELIGIBLE: {rec.title} — {rec.benefits} "
                    f"(Confidence: {rec.confidence*100:.0f}%)"
                )
            elif rec.status == "NEED_MORE_INFO":
                output_parts.append(
                    f"ℹ NEED MORE INFO: {rec.title} — Missing: {', '.join(rec.missing_info)}"
                )

        if not output_parts:
            return "GovernmentSchemeTool output: No matching schemes found for this farmer profile."

        summary = f"Found {eligible_count} eligible scheme(s) out of {len(recommendations)} checked. "
        return f"GovernmentSchemeTool output: {summary}" + " | ".join(output_parts)

    def _build_farmer_profile(self, args: dict[str, Any], container: Any) -> Farmer:
        """Build a Farmer model from available args and context."""
        return Farmer(
            farmer_id=args.get("farmer_id", "unknown"),
            name=args.get("name", "Unknown Farmer"),
            phone_number=args.get("phone_number", "+910000000000"),
            state=args.get("state", "Punjab"),
            district=args.get("district", "Ludhiana"),
            preferred_language=args.get("language", "hi"),
            land_size_hectares=float(args.get("land_size_hectares", 2.0)),
            farmer_category=args.get("farmer_category", "Small"),
            gender=args.get("gender", "Male"),
            caste_category=args.get("caste_category", "General"),
            income_bracket=args.get("income_bracket", "Below 2 Lakh"),
            has_bank_account=args.get("has_bank_account", True),
            has_aadhaar=args.get("has_aadhaar", True),
            active_crops=args.get("active_crops", ["Wheat"]),
            crop_season=args.get("crop_season", "Rabi"),
            is_tenant=args.get("is_tenant", False),
            is_organic=args.get("is_organic", False),
            recent_damage=args.get("recent_damage"),
        )
