"""
test_schemes.py — Sprint 31 Government Schemes Tests.

Verifies:
    1. Scheme catalog and required fields.
    2. Eligibility checks for PM-KISAN, PMFBY, KCC, Soil Health Card, eNAM, and PKVY.
    3. Required document lists (only returns documents actually required).
    4. AI query routing and intent mapping ("subsidy", "scheme", "loan", "insurance").
    5. Integration with IVR (DTMF 1) and SMS outputs.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from app.models.farmer import Farmer
from app.schemes.scheme_service import SchemeService


def _make_farmer(**kwargs: Any) -> Farmer:
    defaults = {
        "farmer_id": "TEST-FARMER-001",
        "name": "Sukhminder Singh",
        "phone_number": "+919876543210",
        "state": "Punjab",
        "district": "Ludhiana",
        "preferred_language": "pa",
        "land_size_hectares": 2.5,
        "soil_type": "Alluvial",
        "water_source": "Tubewell",
        "active_crops": ["Wheat"],
        "farmer_category": "Small",
        "gender": "Male",
        "caste_category": "General",
        "income_bracket": "Below 2 Lakh",
        "has_bank_account": True,
        "has_aadhaar": True,
        "crop_season": "Rabi",
        "is_tenant": False,
        "is_organic": False,
    }
    defaults.update(kwargs)
    return Farmer(**defaults)


# ===========================================================================
# CATALOG & BASIC TESTS
# ===========================================================================

def test_scheme_catalog_completeness() -> None:
    """Verifies that all 6 schemes exist with required metadata fields."""
    service = SchemeService()
    schemes = service.get_all_schemes()
    assert len(schemes) == 6
    expected_ids = {"pm-kisan", "pmfby", "kcc", "soil-health-card", "enam", "pkvy"}
    actual_ids = {s["id"] for s in schemes}
    assert actual_ids == expected_ids

    for s in schemes:
        assert "title" in s
        assert "benefits" in s
        assert "required_documents" in s
        assert "url" in s
        assert "tags" in s


# ===========================================================================
# ELIGIBILITY TESTS
# ===========================================================================

def test_pm_kisan_eligibility() -> None:
    """PM-KISAN eligibility logic: owns land, not tenant, has account + Aadhaar."""
    service = SchemeService()

    # 1. Eligible landowner
    f1 = _make_farmer(land_size_hectares=2.0, is_tenant=False)
    status, reason, _ = service.evaluate_eligibility(f1, "pm-kisan")
    assert status == "Eligible"
    assert "land" in reason.lower()

    # 2. Not eligible: tenant farmer
    f2 = _make_farmer(land_size_hectares=2.0, is_tenant=True)
    status, _, _ = service.evaluate_eligibility(f2, "pm-kisan")
    assert status == "Not Eligible"

    # 3. Not eligible: zero land size
    f3 = _make_farmer(land_size_hectares=0.0, is_tenant=False)
    status, _, _ = service.evaluate_eligibility(f3, "pm-kisan")
    assert status == "Not Eligible"


def test_pmfby_eligibility() -> None:
    """PMFBY: has bank account and active crops."""
    service = SchemeService()

    # 1. Eligible
    f1 = _make_farmer(active_crops=["Wheat"], has_bank_account=True)
    status, _, _ = service.evaluate_eligibility(f1, "pmfby")
    assert status == "Eligible"

    # 2. Possibly Eligible: missing bank account
    f2 = _make_farmer(active_crops=["Wheat"], has_bank_account=False)
    status, reason, _ = service.evaluate_eligibility(f2, "pmfby")
    assert status == "Possibly Eligible"
    assert "bank" in reason.lower()


def test_kcc_eligibility() -> None:
    """KCC credit requirements."""
    service = SchemeService()

    f1 = _make_farmer(active_crops=["Wheat"], has_bank_account=True, has_aadhaar=True)
    status, _, _ = service.evaluate_eligibility(f1, "kcc")
    assert status == "Eligible"


def test_soil_health_card_eligibility() -> None:
    """Soil Health Card: requires land size > 0."""
    service = SchemeService()

    f1 = _make_farmer(land_size_hectares=0.5)
    status, _, _ = service.evaluate_eligibility(f1, "soil-health-card")
    assert status == "Eligible"

    f2 = _make_farmer(land_size_hectares=0.0)
    status, _, _ = service.evaluate_eligibility(f2, "soil-health-card")
    assert status == "Not Eligible"


def test_enam_eligibility() -> None:
    """eNAM trading portal requirements."""
    service = SchemeService()

    f1 = _make_farmer(has_bank_account=True, has_aadhaar=True)
    status, _, _ = service.evaluate_eligibility(f1, "enam")
    assert status == "Eligible"


def test_pkvy_eligibility() -> None:
    """PKVY Organic: minimum 0.4 ha land required."""
    service = SchemeService()

    # 1. Land size too small
    f1 = _make_farmer(land_size_hectares=0.2)
    status, _, _ = service.evaluate_eligibility(f1, "pkvy")
    assert status == "Not Eligible"

    # 2. Eligible organic cultivator
    f2 = _make_farmer(land_size_hectares=1.5, is_organic=True)
    status, _, _ = service.evaluate_eligibility(f2, "pkvy")
    assert status == "Eligible"


# ===========================================================================
# DOCUMENT CHECKS
# ===========================================================================

def test_required_documents_mapping() -> None:
    """Verifies that SchemeService recommendation returns only required documents."""
    service = SchemeService()
    f = _make_farmer()
    recs = service.get_recommendations(f)

    pm_kisan = next(r for r in recs if r.scheme_id == "pm-kisan")
    assert set(pm_kisan.required_documents) == {"Aadhaar", "Bank Passbook", "Land Record", "Mobile Number"}

    soil_card = next(r for r in recs if r.scheme_id == "soil-health-card")
    assert set(soil_card.required_documents) == {"Aadhaar", "Land Record"}
    assert "Bank Passbook" not in soil_card.required_documents


# ===========================================================================
# AI INTEGRATION & INTENT CHECKS
# ===========================================================================

def test_ai_query_routing() -> None:
    """Verifies routing of AI search queries to appropriate schemes (Task 5)."""
    service = SchemeService()

    # "I need subsidy"
    subsidy_schemes = service.route_ai_query("I need subsidy")
    subsidy_ids = {s["id"] for s in subsidy_schemes}
    assert "pm-kisan" in subsidy_ids
    assert "pmfby" in subsidy_ids

    # "Loan"
    loan_schemes = service.route_ai_query("loan help")
    assert len(loan_schemes) == 1
    assert loan_schemes[0]["id"] == "kcc"

    # "Insurance"
    ins_schemes = service.route_ai_query("crop insurance protection")
    assert len(ins_schemes) == 1
    assert ins_schemes[0]["id"] == "pmfby"


# ===========================================================================
# IVR & SMS LOGIC
# ===========================================================================

@pytest.mark.asyncio
async def test_ivr_scheme_dtmf1() -> None:
    """
    DTMF '1' from INTENT_CAPTURE triggers SCHEME_INQUIRY.
    """
    from app.ivr.call_session import CallSession
    from app.ivr.dtmf_handler import DTMFHandler
    from app.ivr.ivr_flow import IVRFlow

    flow = IVRFlow()
    selector = MagicMock()
    handler = DTMFHandler(flow, selector)

    session = CallSession(call_id="ivr-schemes-dtmf1", language="hi")
    session.current_ivr_state = "INTENT_CAPTURE"

    next_state, _ = await handler.handle_dtmf(session, "1")
    assert next_state == "SCHEME_INQUIRY"
    assert session.current_ivr_state == "SCHEME_INQUIRY"
    assert session.metadata.get("intent_query") == "government schemes eligibility"


def test_sms_recommendation_format() -> None:
    """Ensures SMS format includes Scheme Name, Eligibility, and Required Documents."""
    service = SchemeService()
    f = _make_farmer()
    recs = service.get_recommendations(f)
    r = next(rec for rec in recs if rec.scheme_id == "pm-kisan")

    sms_body = (
        f"Scheme: {r.title}\n"
        f"Status: {r.status}\n"
        f"Docs: {', '.join(r.required_documents)}\n"
        f"Link: {r.official_url}"
    )

    assert "PM-KISAN" in sms_body or "Pradhan Mantri" in sms_body
    assert "ELIGIBLE" in sms_body
    assert "Aadhaar" in sms_body
    assert "https://pmkisan.gov.in" in sms_body
