import logging
import time
from typing import Any, Optional

from app.core.context import AgentContext
from app.core.knowledge import KnowledgeProvider

logger = logging.getLogger("kisan_mitra_ai.knowledge.modules.government")


class GovernmentKnowledgeProvider(KnowledgeProvider):
    """
    Catalog holding official government welfare programs and qualifying eligibility rules.
    """
    def __init__(self) -> None:
        self.schemes: list[dict[str, Any]] = [
            {
                "id": "pm-kisan",
                "title": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
                "authority": "Central Government",
                "department": "Department of Agriculture and Farmers Welfare",
                "benefits": "INR 6,000 per year paid in three equal installments of INR 2,000 directly to bank accounts.",
                "eligibility_criteria": ["All landholding farmer families", "Exclude institutional landowners", "Exclude income tax payers"],
                "application_process": "Apply online at pmkisan.gov.in portal or via Common Service Centers (CSC).",
                "required_documents": ["Aadhaar Card", "Landholding Records / Patta", "Bank Account Details"],
                "deadline": "Rolling application, updated quarterly.",
                "tags": ["income support", "money", "subsidy", "financial aid", "central scheme"]
            },
            {
                "id": "pmfby",
                "title": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
                "authority": "Central Government",
                "department": "Ministry of Agriculture",
                "benefits": "Comprehensive crop insurance cover against failure. Premium rate: 2% Kharif, 1.5% Rabi, 5% annual cash crops.",
                "eligibility_criteria": ["All farmers including sharecroppers", "Must grow notified crops in notified areas"],
                "application_process": "Apply via national crop insurance portal (pmfby.gov.in) or local bank branch.",
                "required_documents": ["Land possession certificate", "Sowing certificate", "Aadhaar Card", "Bank passbook"],
                "deadline": "Rabi: December 31st; Kharif: July 31st.",
                "tags": ["insurance", "crop loss", "damage", "premium", "subsidy", "safety net"]
            },
            {
                "id": "soil-health-card",
                "title": "Soil Health Card Scheme",
                "authority": "Central Government",
                "department": "Ministry of Agriculture",
                "benefits": "Provides printed soil reports indicating 12 parameters (NPK, pH, EC, etc.) and corrective dosage recommendations.",
                "eligibility_criteria": ["All farmers possessing cultivable lands"],
                "application_process": "Soil samples collected by local agri officers, cards dispatched to villages.",
                "required_documents": ["Farmer name", "Aadhaar Card", "Soil sample survey ID"],
                "deadline": "Samples collected bi-annually.",
                "tags": ["soil testing", "npk", "fertilizer", "nutrition", "soil card"]
            },
            {
                "id": "kcc",
                "title": "Kisan Credit Card (KCC)",
                "authority": "Central Government / RBI",
                "department": "All Commercial Banks and Co-operatives",
                "benefits": "Flexible short-term credit facility for farming operations and crop cultivation. Interest rate: 4% (with interest subvention).",
                "eligibility_criteria": ["Individual/Joint cultivators", "Tenant farmers", "Sharecroppers", "Self Help Groups"],
                "application_process": "Submit KCC application form to any local public sector bank.",
                "required_documents": ["Identity proof", "Address proof", "Land records", "Sowing proof"],
                "deadline": "No hard deadline, valid for 5 years.",
                "tags": ["credit", "loan", "borrowing", "money", "interest subvention", "finance"]
            }
        ]

    async def search(
        self,
        query: str,
        limit: int = 5,
        context: Optional[AgentContext] = None
    ) -> list[dict[str, Any]]:
        logger.info(f"Government schemes search: '{query}'")
        query_lower = query.lower()
        results = []
        for scheme in self.schemes:
            # Score matches based on content fields
            score = 0.0
            if query_lower in scheme["title"].lower():
                score += 0.8
            if query_lower in scheme["benefits"].lower():
                score += 0.4
            if any(query_lower in tag for tag in scheme["tags"]):
                score += 0.5
            for criterion in scheme["eligibility_criteria"]:
                if query_lower in criterion.lower():
                    score += 0.3

            if score > 0.0:
                results.append({
                    "id": scheme["id"],
                    "title": scheme["title"],
                    "content": f"{scheme['title']} provides: {scheme['benefits']}. Eligibility: {', '.join(scheme['eligibility_criteria'])}.",
                    "metadata": {
                        "authority": scheme["authority"],
                        "department": scheme["department"],
                        "required_documents": scheme["required_documents"],
                        "deadline": scheme["deadline"],
                        "last_updated": time.time()
                    },
                    "score": round(min(score, 1.0), 2),
                    "source": "government_schemes_db"
                })

        results.sort(key=lambda x: float(x["score"]), reverse=True)
        return results[:limit]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        pass

    def health(self) -> dict[str, Any]:
        return {
            "provider": "GovernmentKnowledge",
            "status": "healthy",
            "schemes_count": len(self.schemes)
        }
