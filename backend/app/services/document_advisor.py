"""
Kisan Mitra AI — Document Advisor Service
============================================
Generates per-scheme document guidance for farmers:
  - Required documents
  - Missing documents analysis
  - Application steps
  - Nearest office (district-based)
  - Government department
  - Helpline number
  - Expected timeline
"""
from __future__ import annotations

import logging
from typing import Any

from app.models.farmer import Farmer
from app.models.scheme import SchemeRecommendation

logger = logging.getLogger("kisan_mitra_ai.services.document_advisor")


class DocumentAdvisor:
    """
    Generates comprehensive document and application guidance
    for a farmer based on their scheme eligibility results.
    """

    # Common document descriptions
    DOCUMENT_DESCRIPTIONS: dict[str, str] = {
        "Aadhaar Card": "12-digit Aadhaar identification card issued by UIDAI",
        "Bank Account Details": "Passbook or cancelled cheque with IFSC code",
        "Bank passbook": "Updated bank passbook showing account details",
        "Landholding Records / Patta": "Revenue records showing land ownership (Jamabandi/Patta/7/12 extract)",
        "Land records": "Revenue records showing land ownership",
        "Land records / Patta": "Revenue records showing land ownership (Jamabandi/Patta/7/12 extract)",
        "Land possession certificate": "Certificate from Tehsildar confirming land possession",
        "Sowing certificate": "Certificate from Patwari confirming crop sowing",
        "Sowing proof / Crop certificate": "Certificate from Patwari confirming crop sowing",
        "Mobile Number": "Active mobile number linked to Aadhaar",
        "Crop details": "Details of crops sown including area and variety",
        "Identity proof (Aadhaar)": "Aadhaar card as identity proof",
        "Address proof": "Aadhaar card, voter ID, or utility bill",
        "Passport-size photograph": "Recent passport-size photograph",
        "Age proof": "Birth certificate, school leaving certificate, or Aadhaar",
        "Bank passbook with IFSC": "Bank passbook showing IFSC code and account number",
    }

    def generate_guidance(
        self,
        farmer: Farmer,
        recommendation: SchemeRecommendation,
    ) -> dict[str, Any]:
        """
        Generate complete document and application guidance.
        """
        # Analyze which documents the farmer likely has vs needs
        required = recommendation.required_documents
        has_docs: list[str] = []
        missing_docs: list[str] = []

        for doc in required:
            if self._farmer_likely_has(farmer, doc):
                has_docs.append(doc)
            else:
                missing_docs.append(doc)

        guidance = {
            "scheme_id": recommendation.scheme_id,
            "scheme_title": recommendation.title,
            "status": recommendation.status,
            "required_documents": [
                {
                    "name": doc,
                    "description": self.DOCUMENT_DESCRIPTIONS.get(doc, "Official document"),
                    "status": "available" if doc in has_docs else "needed",
                }
                for doc in required
            ],
            "missing_documents": missing_docs,
            "available_documents": has_docs,
            "application_steps": recommendation.application_steps,
            "nearest_office": recommendation.nearest_office,
            "department": recommendation.department,
            "helpline": recommendation.helpline,
            "official_url": recommendation.official_url,
            "expected_timeline": recommendation.expected_timeline,
            "deadline": recommendation.deadline,
            "tips": self._generate_tips(farmer, recommendation),
        }

        return guidance

    def generate_voice_summary(
        self,
        farmer: Farmer,
        recommendation: SchemeRecommendation,
        language: str = "en",
    ) -> str:
        """
        Generate a natural voice-friendly summary of document requirements in the target language.
        """
        name = farmer.name.split()[0]
        scheme = recommendation.title
        docs = recommendation.required_documents[:3]
        docs_text = ", ".join(docs)
        lang_code = language.split("-", maxsplit=1)[0].lower()

        if lang_code == "hi":
            return (
                f"{name} जी, {scheme} के लिए आवेदन करने के लिए "
                f"कृपया {docs_text} तैयार रखें। "
                f"आवेदन {recommendation.nearest_office} पर करें। "
                f"हेल्पलाइन: {recommendation.helpline}।"
            )
        elif lang_code == "kn":
            return (
                f"{name} ಅವರೇ, {scheme} ಯೋಜನೆಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಲು "
                f"ದಯವಿಟ್ಟು {docs_text} ದಾಖಲೆಗಳನ್ನು ಸಿದ್ಧವಾಗಿಟ್ಟುಕೊಳ್ಳಿ. "
                f"ನಿಮ್ಮ ಹತ್ತಿರದ {recommendation.nearest_office} ಕಚೇರಿಯಲ್ಲಿ ಸಂಪರ್ಕಿಸಿ. "
                f"ಸಹಾಯವಾಣಿ: {recommendation.helpline}."
            )
        elif lang_code == "mr":
            return (
                f"{name} जी, {scheme} साठी अर्ज करण्यासाठी "
                f"कृपया {docs_text} ही कागदपत्रे तयार ठेवा. "
                f"आपल्या जवळच्या {recommendation.nearest_office} कार्यालयात अर्ज करा. "
                f"हेल्पलाइन: {recommendation.helpline}."
            )
        elif lang_code == "pa":
            return (
                f"{name} ਜੀ, {scheme} ਲਈ ਅਰਜ਼ੀ ਦੇਣ ਲਈ "
                f"ਕਿਰਪਾ ਕਰਕੇ {docs_text} ਤਿਆਰ ਰੱਖੋ। "
                f"ਅਰਜ਼ੀ {recommendation.nearest_office} ਤੇ ਦਿਓ। "
                f"ਹੈਲਪਲਾਈਨ: {recommendation.helpline}।"
            )
        else:
            return (
                f"{name}, to apply for {scheme}, "
                f"please keep {docs_text} ready. "
                f"Apply at {recommendation.nearest_office}. "
                f"Helpline: {recommendation.helpline}."
            )


    def _farmer_likely_has(self, farmer: Farmer, doc: str) -> bool:
        """Check if farmer likely already has this document."""
        doc_lower = doc.lower()
        if "aadhaar" in doc_lower:
            return farmer.has_aadhaar
        if "bank" in doc_lower:
            return farmer.has_bank_account
        if "mobile" in doc_lower:
            return bool(farmer.phone_number)
        if "photograph" in doc_lower or "photo" in doc_lower:
            return True  # Most farmers have this
        # Land records, sowing certificates — assume they need to be gathered
        return False

    def _generate_tips(self, farmer: Farmer, rec: SchemeRecommendation) -> list[str]:
        """Generate helpful application tips."""
        tips = []
        if not farmer.has_aadhaar and any("aadhaar" in d.lower() for d in rec.required_documents):
            tips.append("Visit your nearest Aadhaar enrollment center to get your Aadhaar card first.")
        if not farmer.has_bank_account:
            tips.append("Open a Jan Dhan account at any bank — it's free and needed for direct benefit transfer.")
        if farmer.is_tenant:
            tips.append("As a tenant farmer, carry your tenancy agreement as proof of cultivation.")
        if rec.deadline:
            tips.append(f"Important: Submit your application before {rec.deadline}.")
        tips.append(f"For questions, call helpline: {rec.helpline}")
        return tips
