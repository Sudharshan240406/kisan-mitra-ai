"""
scheme_service.py — Production-ready curated Government Scheme Platform for Sprint 31.

Tracks six primary agricultural schemes:
- PM-KISAN
- PMFBY
- KCC
- Soil Health Card
- eNAM
- PKVY

Computes eligibility (Eligible, Possibly Eligible, Not Eligible, Reason)
and maps required documents (Aadhaar, Bank Passbook, Land Record,
Income Certificate, Caste Certificate, Mobile Number).
"""
import logging
from typing import Any

from app.models.farmer import Farmer
from app.models.scheme import SchemeRecommendation

logger = logging.getLogger("kisan_mitra_ai.schemes.scheme_service")

# Curated Schemes Database
CURATED_SCHEMES: list[dict[str, Any]] = [
    {
        "id": "pm-kisan",
        "name": "PM-KISAN",
        "title": "Pradhan Mantri Kisan Samman Nidhi",
        "benefits": "₹6,000 per year paid in three equal installments of ₹2,000 directly to bank accounts.",
        "description": "Income support scheme providing direct cash assistance to landholding farmer families.",
        "required_documents": ["Aadhaar", "Bank Passbook", "Land Record", "Mobile Number"],
        "url": "https://pmkisan.gov.in",
        "helpline": "155261",
        "nearest_office": "Common Service Center (CSC) or District Agriculture Office",
        "department": "Department of Agriculture and Farmers Welfare",
        "tags": ["subsidy", "government scheme", "money", "financial aid", "income support"]
    },
    {
        "id": "pmfby",
        "name": "PMFBY",
        "title": "Pradhan Mantri Fasal Bima Yojana",
        "benefits": "Comprehensive crop insurance cover against crop failure and yield loss due to natural calamities.",
        "description": "Crop insurance scheme safeguarding farmers against unexpected crop damage with low premiums.",
        "required_documents": ["Aadhaar", "Bank Passbook", "Land Record"],
        "url": "https://pmfby.gov.in",
        "helpline": "1800-200-7710",
        "nearest_office": "District Agriculture Office or Local Bank Branch",
        "department": "Ministry of Agriculture",
        "tags": ["insurance", "crop loss", "damage", "bima", "government scheme", "subsidy"]
    },
    {
        "id": "kcc",
        "name": "KCC",
        "title": "Kisan Credit Card",
        "benefits": "Flexible short-term credit/loan up to ₹3 lakh at a concessional interest rate of 4%.",
        "description": "Provides farmers with timely credit for cultivation expenses, post-harvest costs, and allied activities.",
        "required_documents": ["Aadhaar", "Bank Passbook", "Land Record"],
        "url": "https://www.nabard.org",
        "helpline": "Contact nearest bank branch",
        "nearest_office": "Nearest Bank Branch",
        "department": "All Commercial and Co-operative Banks",
        "tags": ["loan", "credit", "borrowing", "money", "finance", "government scheme"]
    },
    {
        "id": "soil-health-card",
        "name": "Soil Health Card",
        "title": "Soil Health Card Scheme",
        "benefits": "Free printed soil test report with 12 parameters and nutrient advice to optimize crop yield.",
        "description": "Promotes balanced fertilizer usage based on scientific testing of local soil samples.",
        "required_documents": ["Aadhaar", "Land Record"],
        "url": "https://soilhealth.dac.gov.in",
        "helpline": "1800-180-1551",
        "nearest_office": "Local Soil Testing Laboratory or Agriculture Extension Center",
        "department": "Ministry of Agriculture",
        "tags": ["soil health card", "soil testing", "npk", "fertilizer", "government scheme"]
    },
    {
        "id": "enam",
        "name": "eNAM",
        "title": "National Agriculture Market",
        "benefits": "Pan-India electronic trading portal integrating APMC mandis for online crop bidding.",
        "description": "Promotes transparent, electronic bidding and price discovery for farmers selling their produce.",
        "required_documents": ["Aadhaar", "Bank Passbook", "Mobile Number"],
        "url": "https://enam.gov.in",
        "helpline": "1800-270-0224",
        "nearest_office": "Nearest APMC Mandi Office",
        "department": "Department of Agriculture",
        "tags": ["enam", "market", "trading", "price discovery", "sell crop", "government scheme"]
    },
    {
        "id": "pkvy",
        "name": "PKVY",
        "title": "Paramparagat Krishi Vikas Yojana",
        "benefits": "₹50,000 per hectare financial support over 3 years for organic farming conversion and PGS certification.",
        "description": "Supports organic farming adoption through cluster-based mobilization, organic inputs, and market linkage.",
        "required_documents": ["Aadhaar", "Land Record", "Income Certificate"],
        "url": "https://pgsindia-ncof.gov.in",
        "helpline": "1800-180-1551",
        "nearest_office": "Regional Centre of Organic Farming (RCOF)",
        "department": "Ministry of Agriculture",
        "tags": ["subsidy", "organic farming", "chemical free", "natural farming", "pkvy", "government scheme"]
    }
]


class SchemeService:
    """
    Curated Government Scheme service implementing eligibility checks,
    intent query routing, and document mappings.
    """

    def get_all_schemes(self) -> list[dict[str, Any]]:
        """Return raw catalog of all 6 curated schemes."""
        return CURATED_SCHEMES

    def get_scheme_by_id(self, scheme_id: str) -> dict[str, Any] | None:
        """Find scheme by ID."""
        for s in CURATED_SCHEMES:
            if s["id"] == scheme_id:
                return s
        return None

    def evaluate_eligibility(self, farmer: Farmer, scheme_id: str) -> tuple[str, str, float]:  # noqa: PLR0911, PLR0912
        """
        Evaluate a farmer's profile against a specific scheme's rules.

        Returns:
            Tuple of (status, reason, confidence)
            Status: "Eligible" | "Possibly Eligible" | "Not Eligible"
        """
        # Lowercase scheme ID lookup
        sid = scheme_id.strip().lower()
        if sid == "pm-kisan":
            # Owns cultivable land, not a tenant, has Aadhaar and bank account
            if farmer.is_tenant:
                return "Not Eligible", "Scheme is exclusively for landowning families, not tenant farmers.", 1.0
            if farmer.land_size_hectares <= 0:
                return "Not Eligible", "Cultivable land ownership is required for PM-KISAN.", 1.0
            if not farmer.has_aadhaar or not farmer.has_bank_account:
                return "Possibly Eligible", "Eligible, but requires linked Aadhaar and bank account verification.", 0.85
            return "Eligible", "Farmer owns cultivable land and holds linked bank and Aadhaar accounts.", 1.0

        elif sid == "pmfby":
            # Insurable crops and bank account
            if not farmer.active_crops:
                return "Possibly Eligible", "Active crops could not be verified in profile.", 0.7
            if not farmer.has_bank_account:
                return "Possibly Eligible", "Requires active bank account for premium auto-deduction.", 0.8
            return "Eligible", "Active crop cultivation and bank account confirmed.", 1.0

        elif sid == "kcc":
            # Concessional credit: needs active crops, bank account, and Aadhaar
            if not farmer.active_crops:
                return "Possibly Eligible", "Crop sowing verification required to evaluate credit limit.", 0.75
            if not farmer.has_bank_account or not farmer.has_aadhaar:
                return "Possibly Eligible", "Bank account and Aadhaar KYC required for bank enrollment.", 0.85
            return "Eligible", "Active crop cultivation, Aadhaar KYC, and bank account verified.", 1.0

        elif sid == "soil-health-card":
            # Needs cultivable land
            if farmer.land_size_hectares <= 0:
                return "Not Eligible", "Cultivable land required for soil sampling.", 1.0
            return "Eligible", "Farmer possesses cultivable land ready for soil profiling.", 1.0

        elif sid == "enam":
            # Electronic trading: needs bank account and Aadhaar for registration
            if not farmer.has_bank_account or not farmer.has_aadhaar:
                return "Possibly Eligible", "Aadhaar and bank account details required for online bidding registration.", 0.8
            return "Eligible", "Verified Aadhaar and bank account details for trading portal.", 1.0

        elif sid == "pkvy":
            # Organic farming cluster: land size >= 0.4 ha
            if farmer.land_size_hectares < 0.4:
                return "Not Eligible", "PKVY requires a minimum land holding of 0.4 hectares (1 acre) for cluster certification.", 1.0
            if not farmer.is_organic:
                return "Possibly Eligible", "Must participate in organic cluster transition group.", 0.8
            return "Eligible", "Practices organic farming with eligible landholding size.", 1.0

        # Fallback default
        return "Possibly Eligible", "Meets general farming demographic criteria.", 0.5

    def get_recommendations(self, farmer: Farmer) -> list[SchemeRecommendation]:
        """
        Evaluate farmer against all 6 curated schemes and return SchemeRecommendations.
        """
        recommendations = []
        for s in CURATED_SCHEMES:
            status, reason, confidence = self.evaluate_eligibility(farmer, s["id"])

            # Map status to SchemeRecommendation values:
            # "Eligible" -> "ELIGIBLE"
            # "Possibly Eligible" -> "POSSIBLY_ELIGIBLE"
            # "Not Eligible" -> "NOT_ELIGIBLE"
            rec_status = "ELIGIBLE"
            if status == "Possibly Eligible":
                rec_status = "POSSIBLY_ELIGIBLE"
            elif status == "Not Eligible":
                rec_status = "NOT_ELIGIBLE"

            # Filter documents to only return those required
            docs = list(s["required_documents"])

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

        return recommendations

    def route_ai_query(self, query: str) -> list[dict[str, Any]]:
        """
        Match AI query to matching schemes based on keyword tags.
        """
        q = query.strip().lower()
        matched = []

        # Tag mappings for TASK 5 keywords
        # "I need subsidy" -> PM-KISAN, PMFBY, PKVY, Soil Health Card
        # "Government scheme" -> matches all
        # "Loan" -> KCC
        # "Insurance" -> PMFBY
        for s in CURATED_SCHEMES:
            score = 0.0
            if "scheme" in q or "yojana" in q:
                score += 0.5
            if "subsidy" in q and s["id"] in ("pm-kisan", "pmfby", "pkvy", "soil-health-card"):
                score += 0.8
            if "loan" in q and s["id"] == "kcc":
                score += 1.0
            if "insurance" in q and s["id"] == "pmfby":
                score += 1.0

            # Tag or title match
            for tag in s["tags"]:
                if tag in q:
                    score += 0.6

            if score > 0.0 or q in s["title"].lower():
                matched.append(s)

        # Fallback: if nothing matches but query mentions "government", return all
        if not matched and ("government" in q or "scheme" in q or "सहायता" in q):
            return CURATED_SCHEMES

        return matched
