"""
Kisan Mitra AI — Explainable Eligibility Engine
==================================================
Evaluates a farmer's Digital Twin profile against structured
government scheme eligibility rules and produces an explainable verdict.

Output statuses:
  ELIGIBLE           — farmer meets all criteria
  POSSIBLY_ELIGIBLE  — farmer meets most criteria, some optional rules failed
  NEED_MORE_INFO     — critical profile fields are missing
  NOT_ELIGIBLE       — farmer fails required eligibility rules
"""
from __future__ import annotations

import logging
import time
from typing import Any

from app.models.farmer import Farmer
from app.models.scheme import EligibilityRule, SchemeRecommendation

logger = logging.getLogger("kisan_mitra_ai.services.eligibility")


class EligibilityEngine:
    """
    Rule-based eligibility evaluator with reasoning transparency.
    Every decision includes a step-by-step reasoning chain.
    """

    # District → nearest office mapping (demo subset)
    DISTRICT_OFFICES: dict[str, str] = {
        "Ludhiana": "District Agriculture Office, Civil Lines, Ludhiana",
        "Amritsar": "District Agriculture Office, Ranjit Avenue, Amritsar",
        "Jaipur": "Krishi Bhawan, Lal Kothi, Jaipur",
        "Nagpur": "District Agriculture Superintendent Office, Civil Lines, Nagpur",
        "Dharwad": "Joint Director of Agriculture, Dharwad",
        "Bhopal": "Department of Farmer Welfare, Mantralaya, Bhopal",
        "Indore": "District Agriculture Office, Indore",
    }

    def __init__(self) -> None:
        self._evaluations_count: int = 0
        self._avg_latency_ms: float = 0.0

    def evaluate(
        self,
        farmer: Farmer,
        scheme_data: dict[str, Any],
    ) -> SchemeRecommendation:
        """
        Evaluate a single farmer against a single scheme.
        Returns a SchemeRecommendation with explainable reasoning.
        """
        start = time.perf_counter()
        reasoning: list[str] = []
        evidence: list[str] = []
        missing_info: list[str] = []
        passed_required = 0
        failed_required = 0
        passed_optional = 0
        failed_optional = 0
        total_required = 0
        total_optional = 0

        rules = scheme_data.get("eligibility_rules", [])
        if not rules:
            # No structured rules — fall back to text matching
            reasoning.append("No structured eligibility rules defined; using text-based heuristic.")
            status = "POSSIBLY_ELIGIBLE"
            confidence = 0.5
        else:
            for rule_data in rules:
                rule = EligibilityRule(**rule_data) if isinstance(rule_data, dict) else rule_data
                result = self._evaluate_rule(farmer, rule)

                if rule.required:
                    total_required += 1
                else:
                    total_optional += 1

                if result == "PASS":
                    reasoning.append(f"✓ {rule.description}")
                    evidence.append(f"Farmer profile field '{rule.field}' satisfies rule.")
                    if rule.required:
                        passed_required += 1
                    else:
                        passed_optional += 1
                elif result == "MISSING":
                    reasoning.append(f"? {rule.description} — information not available")
                    missing_info.append(rule.field)
                    if rule.required:
                        failed_required += 1
                    else:
                        failed_optional += 1
                else:
                    reasoning.append(f"✗ {rule.description}")
                    if rule.required:
                        failed_required += 1
                    else:
                        failed_optional += 1

            # Determine status
            if failed_required == 0 and not missing_info:
                status = "ELIGIBLE"
                confidence = 0.95 if failed_optional == 0 else 0.85
            elif failed_required == 0 and missing_info:
                status = "NEED_MORE_INFO"
                confidence = 0.6
            elif failed_required <= 1 and total_required > 2:
                status = "POSSIBLY_ELIGIBLE"
                confidence = 0.55
            else:
                status = "NOT_ELIGIBLE"
                confidence = 0.9

        # State applicability check
        state_list = scheme_data.get("state_applicability", [])
        if state_list and farmer.state not in state_list:
            reasoning.append(f"✗ Scheme not available in {farmer.state}.")
            status = "NOT_ELIGIBLE"
            confidence = 0.95

        # Build recommendation
        nearest_office = self.DISTRICT_OFFICES.get(
            farmer.district,
            scheme_data.get("nearest_office", f"District Agriculture Office, {farmer.district}")
        )

        # Determine missing documents
        required_docs = scheme_data.get("required_documents", [])
        missing_docs: list[str] = []
        if not farmer.has_aadhaar and "Aadhaar Card" in required_docs:
            missing_docs.append("Aadhaar Card")
        if not farmer.has_bank_account and any("Bank" in d for d in required_docs):
            missing_docs.append("Bank Account Details")

        latency_ms = (time.perf_counter() - start) * 1000
        self._evaluations_count += 1
        self._avg_latency_ms = (
            (self._avg_latency_ms * (self._evaluations_count - 1) + latency_ms)
            / self._evaluations_count
        )

        reasoning.append(f"Evaluation completed in {latency_ms:.1f}ms. Status: {status}.")
        evidence.append(f"Source: Government Schemes Knowledge Base (scheme_id: {scheme_data.get('id', 'unknown')})")

        return SchemeRecommendation(
            scheme_id=scheme_data.get("id", "unknown"),
            title=scheme_data.get("title", "Unknown Scheme"),
            status=status,
            confidence=round(confidence, 2),
            reasoning=reasoning,
            evidence=evidence,
            benefits=scheme_data.get("benefits", ""),
            required_documents=required_docs,
            missing_documents=missing_docs,
            deadline=scheme_data.get("deadline", ""),
            department=scheme_data.get("department", ""),
            helpline=scheme_data.get("helpline", ""),
            nearest_office=nearest_office,
            official_url=scheme_data.get("official_url", ""),
            application_steps=scheme_data.get("application_steps", []),
            expected_timeline=scheme_data.get("expected_timeline", "4-6 weeks"),
            missing_info=missing_info,
        )

    def evaluate_all(
        self,
        farmer: Farmer,
        schemes: list[dict[str, Any]],
    ) -> list[SchemeRecommendation]:
        """Evaluate a farmer against all available schemes."""
        results = []
        for scheme in schemes:
            rec = self.evaluate(farmer, scheme)
            results.append(rec)

        # Sort: ELIGIBLE first, then POSSIBLY_ELIGIBLE, then NEED_MORE_INFO, then NOT_ELIGIBLE
        priority = {"ELIGIBLE": 0, "POSSIBLY_ELIGIBLE": 1, "NEED_MORE_INFO": 2, "NOT_ELIGIBLE": 3}
        results.sort(key=lambda r: (priority.get(r.status, 4), -r.confidence))
        return results

    def _evaluate_rule(self, farmer: Farmer, rule: EligibilityRule) -> str:
        """
        Evaluate a single rule against the farmer profile.
        Returns: 'PASS', 'FAIL', or 'MISSING'.
        """
        farmer_dict = farmer.model_dump()
        field_val = farmer_dict.get(rule.field)

        if field_val is None and rule.operator != "exists":
            return "MISSING"

        op = rule.operator
        expected = rule.value

        if op == "exists":
            return "PASS" if field_val is not None else "MISSING"
        elif op == "eq":
            return "PASS" if field_val == expected else "FAIL"
        elif op == "ne":
            return "PASS" if field_val != expected else "FAIL"
        elif op == "lt":
            return "PASS" if float(field_val) < float(expected) else "FAIL"
        elif op == "lte":
            return "PASS" if float(field_val) <= float(expected) else "FAIL"
        elif op == "gt":
            return "PASS" if float(field_val) > float(expected) else "FAIL"
        elif op == "gte":
            return "PASS" if float(field_val) >= float(expected) else "FAIL"
        elif op == "in":
            if isinstance(expected, list):
                return "PASS" if field_val in expected else "FAIL"
            return "FAIL"
        elif op == "not_in":
            if isinstance(expected, list):
                return "PASS" if field_val not in expected else "FAIL"
            return "PASS"
        elif op == "any":
            # field is a list, check if any element is in expected
            if isinstance(field_val, list) and isinstance(expected, list):
                return "PASS" if any(v in expected for v in field_val) else "FAIL"
            return "FAIL"
        elif op == "bool_true":
            return "PASS" if field_val is True else "FAIL"
        elif op == "bool_false":
            return "PASS" if field_val is False else "FAIL"
        else:
            logger.warning(f"Unknown operator '{op}' in eligibility rule.")
            return "MISSING"

    def health(self) -> dict[str, Any]:
        return {
            "engine": "EligibilityEngine",
            "status": "healthy",
            "evaluations_count": self._evaluations_count,
            "avg_latency_ms": round(self._avg_latency_ms, 2),
        }
