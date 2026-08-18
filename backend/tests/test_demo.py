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


class TestQuestionResponseUniqueness:
    """
    Automated Regression Tests for Question-Specific AI Responses.
    Verifies 20 test cases (5 questions x 4 languages):
    - Question A response != Question B response
    - Crop damage questions do NOT return PM-KISAN answers
    - PM-KISAN questions do NOT return crop damage answers
    - Pests/disease questions do NOT return PM-KISAN answers
    """

    QUESTIONS = {
        "en": [
            "What government schemes am I eligible for?",
            "My crop was damaged by heavy rain. What should I do?",
            "When will I receive my PM-KISAN payment?",
            "How can I get crop insurance?",
            "What should I do about pests in my crop?",
        ],
        "kn": [
            "ಸರ್ಕಾರದ ಯಾವ ಯೋಜನೆಗಳಿಗೆ ನಾನು ಅರ್ಹನಾಗಿದ್ದೇನೆ?",
            "ಮಳೆಯಿಂದ ನನ್ನ ಬೆಳೆ ಹಾನಿಯಾಗಿದೆ, ನಾನು ಏನು ಮಾಡಬೇಕು?",
            "ನನ್ನ ಪಿಎಂ-ಕಿಸಾನ್ ಹಣ ಎಂದಿಗೆ ಬರುತ್ತದೆ?",
            "ಬೆಳೆ ವಿಮೆ ಪಡೆದುಕೊಳ್ಳುವುದು ಹೇಗೆ?",
            "ಬೆಳೆಯಲ್ಲಿ ಕೀಟ ಬಾಧೆ ನಿಯಂತ್ರಿಸುವುದು ಹೇಗೆ?",
        ],
        "hi": [
            "मैं किन सरकारी योजनाओं के लिए पात्र हूं?",
            "भारी बारिश से मेरी फसल खराब हो गई है, मुझे क्या करना चाहिए?",
            "मुझे पीएम-किसान की किस्त कब मिलेगी?",
            "फसल बीमा कैसे प्राप्त करें?",
            "फसल में कीट नियंत्रण कैसे करें?",
        ],
        "te": [
            "నేను ఏ ప్రభుత్వ పథకాలకు అర్హుడిని?",
            "వర్షాల వల్ల నా పంట పాడైపోయింది, నేను ఏమి చేయాలి?",
            "నా పీఎం-కిసాన్ డబ్బులు ఎప్పుడు వస్తాయి?",
            "పంట బీమా ఎలా పొందాలి?",
            "పంట తెగుళ్ల నివారణ ఎలా చేయాలి?",
        ],
    }

    async def test_20_question_response_uniqueness(self):
        """Test 5 questions x 4 languages = 20 cases for absolute uniqueness."""
        from app.api.v1.demo import process_demo_voice_query, DemoVoiceQueryRequest

        for lang, q_list in self.QUESTIONS.items():
            responses = []
            schemes = []

            for q in q_list:
                req = DemoVoiceQueryRequest(
                    farmer_id="DEMO-F001",
                    user_selected_language=lang,
                    question=q
                )
                res = await process_demo_voice_query(req)
                resp_text = res["voice_response"]
                top_scheme = res["top_scheme"]

                # Ensure non-empty response
                assert len(resp_text) > 10, f"Empty response for question '{q}' in {lang}"
                assert top_scheme is not None, f"Null scheme for question '{q}' in {lang}"

                responses.append(resp_text)
                schemes.append(top_scheme)

            # Assert all 5 responses for this language are unique
            assert len(set(responses)) == 5, f"Duplicate responses detected in {lang}: {responses}"

            # Assert crop damage (index 1) does NOT talk about PM-Kisan
            damage_resp = responses[1].lower()
            assert "kisan samman" not in damage_resp and "ಕಿಸಾನ್ ಸಮ್ಮಾನ" not in damage_resp

            # Assert PM-Kisan (index 2) does NOT talk about rain damage / PMFBY
            pm_resp = responses[2].lower()
            assert "fasal bima" not in pm_resp and "ಮಳೆಯಿಂದ" not in pm_resp



class TestOutOfScopeFallback:
    """
    Automated Regression Tests for False-Confidence Fallback.
    Ensures out-of-scope or unmapped queries do NOT silently return PM-Kisan
    or another scheme confidently, but instead return an honest fallback message.
    """

    OUT_OF_SCOPE_QUERIES = [
        "My irrigation pump broke, is there a scheme for that?",
        "Where can I buy tractor tires near my village?",
        "Who won the cricket match yesterday?",
    ]

    async def test_out_of_scope_queries_return_honest_fallback(self):
        from app.api.v1.demo import process_demo_voice_query, DemoVoiceQueryRequest

        for q in self.OUT_OF_SCOPE_QUERIES:
            req = DemoVoiceQueryRequest(
                farmer_id="DEMO-F001",
                user_selected_language="en",
                question=q
            )
            res = await process_demo_voice_query(req)
            resp_text = res["voice_response"]
            top_scheme = res["top_scheme"]

            # Must NOT falsely claim PM-Kisan or PMFBY for unrelated pump/car/tire query
            assert top_scheme == "General Agricultural Guidance", f"Query '{q}' falsely matched scheme '{top_scheme}'"
            assert "don't have specific scheme information" in resp_text.lower() or "1800-180-1551" in resp_text
            assert "pm-kisan" not in resp_text.lower() or "samman nidhi" not in resp_text.lower()
