"""
Phase 15 — Demo Service & API Tests
======================================
Tests demo farmer profiles, simulation, and document advisor.
"""

from app.knowledge.modules.government import GovernmentKnowledgeProvider
from app.models.scheme import SchemeRecommendation
from app.services.demo import DEMO_FARMERS, DemoService
from app.services.document_advisor import DocumentAdvisor
from app.services.eligibility import EligibilityEngine
from app.services.scheme_service import GovernmentSchemeService


class TestDemoService:
    """Tests for the demo farmer profile service."""

    def test_has_six_farmers(self):
        service = DemoService()
        farmers = service.get_all_farmers()
        assert len(farmers) == 6

    def test_each_farmer_unique_id(self):
        service = DemoService()
        farmers = service.get_all_farmers()
        ids = [f.farmer_id for f in farmers]
        assert len(ids) == len(set(ids))

    def test_each_farmer_unique_phone(self):
        service = DemoService()
        farmers = service.get_all_farmers()
        phones = [f.phone_number for f in farmers]
        assert len(phones) == len(set(phones))

    def test_get_farmer_by_id(self):
        service = DemoService()
        farmer = service.get_farmer("DEMO-F001")
        assert farmer is not None
        assert farmer.name == "Ramesh Singh"

    def test_get_farmer_by_phone(self):
        service = DemoService()
        farmer = service.get_farmer_by_phone("+919876543210")
        assert farmer is not None
        assert farmer.farmer_id == "DEMO-F001"

    def test_get_farmer_not_found(self):
        service = DemoService()
        assert service.get_farmer("NONEXISTENT") is None
        assert service.get_farmer_by_phone("+910000000000") is None

    def test_farmer_summary_fields(self):
        service = DemoService()
        farmer = service.get_farmer("DEMO-F001")
        assert farmer is not None
        summary = service.get_farmer_summary(farmer)
        required_keys = ["farmer_id", "name", "phone", "state", "district", "category", "gender", "land_hectares", "crops", "language"]
        for key in required_keys:
            assert key in summary, f"Missing key: {key}"

    def test_diverse_farmer_categories(self):
        """Demo farmers should cover multiple categories."""
        service = DemoService()
        farmers = service.get_all_farmers()
        categories = set(f.farmer_category for f in farmers)
        assert len(categories) >= 2

    def test_diverse_genders(self):
        """Demo farmers should include both male and female."""
        service = DemoService()
        farmers = service.get_all_farmers()
        genders = set(f.gender for f in farmers)
        assert "Male" in genders
        assert "Female" in genders

    def test_diverse_states(self):
        """Demo farmers should come from multiple states."""
        service = DemoService()
        farmers = service.get_all_farmers()
        states = set(f.state for f in farmers)
        assert len(states) >= 3

    def test_generate_call_transcript(self):
        service = DemoService()
        engine = EligibilityEngine()
        provider = GovernmentKnowledgeProvider()
        farmer = service.get_farmer("DEMO-F001")
        assert farmer is not None
        schemes = provider.get_all_schemes()
        recs = engine.evaluate_all(farmer, schemes)
        rec_dicts = [r.model_dump() for r in recs]
        transcript = service.generate_call_transcript(farmer, rec_dicts)
        assert len(transcript) > 0
        roles = {t["role"] for t in transcript}
        assert "assistant" in roles
        assert "system" in roles


class TestDocumentAdvisor:
    """Tests for the document advisor service."""

    def test_generate_guidance(self):
        advisor = DocumentAdvisor()
        farmer = DEMO_FARMERS[0]
        rec = SchemeRecommendation(
            scheme_id="pm-kisan",
            title="PM-KISAN",
            status="ELIGIBLE",
            confidence=0.95,
            benefits="INR 6,000/year",
            required_documents=["Aadhaar Card", "Bank Account Details", "Land Records"],
            deadline="Rolling",
            helpline="155261",
            nearest_office="CSC Center",
            application_steps=["Visit CSC", "Fill form", "Submit"],
        )
        guidance = advisor.generate_guidance(farmer, rec)
        assert "scheme_id" in guidance
        assert "required_documents" in guidance
        assert "tips" in guidance
        assert len(guidance["required_documents"]) > 0

    def test_generate_voice_summary_hindi(self):
        advisor = DocumentAdvisor()
        farmer = DEMO_FARMERS[0]
        rec = SchemeRecommendation(
            scheme_id="pm-kisan",
            title="PM-KISAN",
            status="ELIGIBLE",
            confidence=0.95,
            required_documents=["Aadhaar Card", "Bank Details"],
            deadline="Rolling",
            helpline="155261",
            nearest_office="CSC Center",
        )
        summary = advisor.generate_voice_summary(farmer, rec, "hi")
        assert len(summary) > 0
        assert "Ramesh" in summary or "PM-KISAN" in summary

    def test_generate_voice_summary_english(self):
        advisor = DocumentAdvisor()
        farmer = DEMO_FARMERS[3]  # Priya Kumari
        rec = SchemeRecommendation(
            scheme_id="organic-farming",
            title="PKVY",
            status="ELIGIBLE",
            confidence=0.85,
            required_documents=["Land records", "Aadhaar Card"],
            deadline="Rolling",
            helpline="1800-180-1551",
            nearest_office="RCOF",
        )
        summary = advisor.generate_voice_summary(farmer, rec, "en")
        assert "Priya" in summary

    def test_missing_docs_detected(self):
        advisor = DocumentAdvisor()
        # Create farmer without aadhaar
        from app.models.farmer import Farmer
        farmer = Farmer(
            farmer_id="TEST",
            name="Test Farmer",
            phone_number="+910000",
            state="Punjab",
            district="Ludhiana",
            land_size_hectares=1.0,
            has_aadhaar=False,
            has_bank_account=False,
        )
        rec = SchemeRecommendation(
            scheme_id="pm-kisan",
            title="PM-KISAN",
            status="NEED_MORE_INFO",
            required_documents=["Aadhaar Card", "Bank Account Details"],
        )
        guidance = advisor.generate_guidance(farmer, rec)
        assert "Aadhaar Card" in guidance["missing_documents"]
        assert "Bank Account Details" in guidance["missing_documents"]


class TestGovernmentSchemeService:
    """Tests for the scheme service orchestration layer."""

    def test_evaluate_farmer_eligibility(self):
        service = GovernmentSchemeService()
        provider = GovernmentKnowledgeProvider()
        farmer = DEMO_FARMERS[0]
        schemes = provider.get_all_schemes()
        results = service.evaluate_farmer_eligibility(farmer, schemes)
        assert len(results) > 0

    def test_generate_voice_response_hi(self):
        service = GovernmentSchemeService()
        provider = GovernmentKnowledgeProvider()
        farmer = DEMO_FARMERS[0]
        schemes = provider.get_all_schemes()
        results = service.evaluate_farmer_eligibility(farmer, schemes)
        voice = service.generate_voice_response(farmer, results, "hi")
        assert len(voice) > 0
        assert "Ramesh" in voice

    def test_generate_voice_response_en(self):
        service = GovernmentSchemeService()
        provider = GovernmentKnowledgeProvider()
        farmer = DEMO_FARMERS[3]  # Priya Kumari
        schemes = provider.get_all_schemes()
        results = service.evaluate_farmer_eligibility(farmer, schemes)
        voice = service.generate_voice_response(farmer, results, "en")
        assert len(voice) > 0

    def test_no_schemes_response(self):
        service = GovernmentSchemeService()
        voice = service.generate_voice_response(DEMO_FARMERS[0], [], "en")
        assert "no matching" in voice.lower() or "not found" in voice.lower() or "contact" in voice.lower()
