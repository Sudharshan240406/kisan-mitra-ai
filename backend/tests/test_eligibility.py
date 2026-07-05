"""
Phase 15 — Eligibility Engine Tests
======================================
Tests the explainable eligibility engine against all demo farmer profiles.
"""
import pytest

from app.models.farmer import Farmer
from app.services.eligibility import EligibilityEngine
from app.knowledge.modules.government import GovernmentKnowledgeProvider
from app.services.demo import DEMO_FARMERS, DemoService


@pytest.fixture
def engine():
    return EligibilityEngine()


@pytest.fixture
def schemes():
    return GovernmentKnowledgeProvider().get_all_schemes()


@pytest.fixture
def demo_service():
    return DemoService()


class TestEligibilityEngine:
    """Core eligibility engine evaluation tests."""

    def test_engine_instantiation(self, engine):
        assert engine is not None
        health = engine.health()
        assert health["engine"] == "EligibilityEngine"
        assert health["status"] == "healthy"

    def test_evaluate_single_scheme(self, engine, schemes):
        """Evaluate Ramesh Singh (Small, Punjab, Wheat) against PM-KISAN."""
        farmer = DEMO_FARMERS[0]  # Ramesh Singh
        pm_kisan = next(s for s in schemes if s["id"] == "pm-kisan")
        result = engine.evaluate(farmer, pm_kisan)

        assert result.scheme_id == "pm-kisan"
        assert result.status in ["ELIGIBLE", "POSSIBLY_ELIGIBLE", "NEED_MORE_INFO", "NOT_ELIGIBLE"]
        assert result.confidence > 0.0
        assert len(result.reasoning) > 0
        assert len(result.evidence) > 0

    def test_evaluate_all_schemes(self, engine, schemes):
        """Evaluate Ramesh Singh against all 11 schemes."""
        farmer = DEMO_FARMERS[0]
        results = engine.evaluate_all(farmer, schemes)

        assert len(results) == len(schemes)
        # Results should be sorted: ELIGIBLE first
        statuses = [r.status for r in results]
        if "ELIGIBLE" in statuses:
            first_eligible_idx = statuses.index("ELIGIBLE")
            # All ELIGIBLE should come before non-ELIGIBLE
            for i, s in enumerate(statuses):
                if s == "ELIGIBLE":
                    assert i <= first_eligible_idx + sum(1 for x in statuses if x == "ELIGIBLE")

    def test_ramesh_gets_pm_kisan(self, engine, schemes):
        """Ramesh Singh (Small, Punjab, 2ha, landowner) should be eligible for PM-KISAN."""
        farmer = DEMO_FARMERS[0]
        pm_kisan = next(s for s in schemes if s["id"] == "pm-kisan")
        result = engine.evaluate(farmer, pm_kisan)
        assert result.status == "ELIGIBLE"
        assert result.confidence >= 0.8

    def test_lakshmi_gets_mahila_kisan(self, engine, schemes):
        """Lakshmi Devi (Female, Marginal) should be eligible for Mahila Kisan."""
        farmer = DEMO_FARMERS[1]  # Lakshmi Devi
        mahila = next(s for s in schemes if s["id"] == "mahila-kisan")
        result = engine.evaluate(farmer, mahila)
        assert result.status == "ELIGIBLE"

    def test_gopal_tenant_status(self, engine, schemes):
        """Gopal Yadav (Tenant) — PM-KISAN optional rule for tenants."""
        farmer = DEMO_FARMERS[2]  # Gopal Yadav
        pm_kisan = next(s for s in schemes if s["id"] == "pm-kisan")
        result = engine.evaluate(farmer, pm_kisan)
        # Tenant rule is optional, so should still pass
        assert result.status in ["ELIGIBLE", "POSSIBLY_ELIGIBLE"]

    def test_priya_organic_scheme(self, engine, schemes):
        """Priya Kumari (Organic, 3ha) should match organic farming scheme."""
        farmer = DEMO_FARMERS[3]  # Priya Kumari
        organic = next(s for s in schemes if s["id"] == "organic-farming")
        result = engine.evaluate(farmer, organic)
        assert result.status == "ELIGIBLE"

    def test_mohammed_crop_insurance(self, engine, schemes):
        """Mohammed Rafi (Rain-Damaged, Cotton) should match PMFBY."""
        farmer = DEMO_FARMERS[4]  # Mohammed Rafi
        pmfby = next(s for s in schemes if s["id"] == "pmfby")
        result = engine.evaluate(farmer, pmfby)
        assert result.status == "ELIGIBLE"

    def test_harpreet_pm_kmy_pension(self, engine, schemes):
        """Harpreet Kaur (Small, 1.5ha) should be eligible for PM-KMY pension."""
        farmer = DEMO_FARMERS[5]  # Harpreet Kaur
        pmkmy = next(s for s in schemes if s["id"] == "pmkmy")
        result = engine.evaluate(farmer, pmkmy)
        assert result.status == "ELIGIBLE"

    def test_male_farmer_not_eligible_mahila(self, engine, schemes):
        """Male farmers should NOT be eligible for Mahila Kisan (women-only)."""
        farmer = DEMO_FARMERS[0]  # Ramesh Singh (Male)
        mahila = next(s for s in schemes if s["id"] == "mahila-kisan")
        result = engine.evaluate(farmer, mahila)
        assert result.status == "NOT_ELIGIBLE"

    def test_each_demo_farmer_has_some_eligible_schemes(self, engine, schemes):
        """Every demo farmer should have at least 1 eligible scheme."""
        for farmer in DEMO_FARMERS:
            results = engine.evaluate_all(farmer, schemes)
            eligible = [r for r in results if r.status == "ELIGIBLE"]
            assert len(eligible) >= 1, f"{farmer.name} has no eligible schemes"

    def test_reasoning_chain_not_empty(self, engine, schemes):
        """Every evaluation should produce a non-empty reasoning chain."""
        farmer = DEMO_FARMERS[0]
        for scheme in schemes:
            result = engine.evaluate(farmer, scheme)
            assert len(result.reasoning) > 0, f"No reasoning for scheme {scheme['id']}"

    def test_confidence_in_valid_range(self, engine, schemes):
        """Confidence should always be between 0 and 1."""
        for farmer in DEMO_FARMERS:
            for scheme in schemes:
                result = engine.evaluate(farmer, scheme)
                assert 0.0 <= result.confidence <= 1.0

    def test_documents_populated(self, engine, schemes):
        """Eligible schemes should have required_documents populated."""
        farmer = DEMO_FARMERS[0]
        results = engine.evaluate_all(farmer, schemes)
        eligible = [r for r in results if r.status == "ELIGIBLE"]
        for r in eligible:
            assert len(r.required_documents) > 0

    def test_health_updates_after_evaluations(self, engine, schemes):
        """Health should track evaluation count."""
        farmer = DEMO_FARMERS[0]
        engine.evaluate_all(farmer, schemes)
        health = engine.health()
        assert health["evaluations_count"] > 0


class TestGovernmentKnowledgeProvider:
    """Tests for the Government Knowledge Provider."""

    def test_has_11_schemes(self):
        provider = GovernmentKnowledgeProvider()
        assert len(provider.schemes) == 11

    @pytest.mark.asyncio
    async def test_search_by_keyword(self):
        provider = GovernmentKnowledgeProvider()
        results = await provider.search("insurance")
        assert len(results) >= 1
        assert any("PMFBY" in r["title"] or "Bima" in r["title"] for r in results)

    @pytest.mark.asyncio
    async def test_search_by_credit(self):
        provider = GovernmentKnowledgeProvider()
        results = await provider.search("credit")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_returns_metadata(self):
        provider = GovernmentKnowledgeProvider()
        results = await provider.search("income support")
        for r in results:
            assert "metadata" in r
            assert "authority" in r["metadata"]

    def test_get_scheme_by_id(self):
        provider = GovernmentKnowledgeProvider()
        scheme = provider.get_scheme_by_id("pm-kisan")
        assert scheme is not None
        assert scheme["title"] == "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)"

    def test_get_scheme_by_id_not_found(self):
        provider = GovernmentKnowledgeProvider()
        assert provider.get_scheme_by_id("nonexistent") is None

    def test_all_schemes_have_eligibility_rules(self):
        provider = GovernmentKnowledgeProvider()
        for scheme in provider.schemes:
            assert "eligibility_rules" in scheme, f"Scheme {scheme['id']} missing eligibility_rules"
            assert len(scheme["eligibility_rules"]) > 0, f"Scheme {scheme['id']} has no rules"

    def test_health(self):
        provider = GovernmentKnowledgeProvider()
        health = provider.health()
        assert health["status"] == "healthy"
        assert health["schemes_count"] == 11
