"""
Kisan Mitra AI — Human Escalation Engine
==========================================
The HumanEscalationEngine implements a rule-based safety layer that determines
when an AI advisory must be escalated to a human expert.

Escalation triggers (any one is sufficient):
  1. Overall confidence < CONFIDENCE_THRESHOLD (default: 0.30)
  2. Unresolved critical conflicts in evidence
  3. Safety-critical keywords detected in the advisory or query
  4. More than MAX_MISSING_FIELDS_BEFORE_ESCALATE missing query fields
  5. Evidence count falls below minimum threshold

When escalation is triggered:
  - The escalation reason is recorded.
  - A structured escalation packet is assembled for routing to a KVK expert.
  - The session is flagged as `escalated=True`.
  - The platform emits an escalation event to the monitoring bus.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

logger = logging.getLogger("kisan_mitra_ai.reasoning.escalation")

# ---------------------------------------------------------------------------
# Escalation Configuration
# ---------------------------------------------------------------------------
_CONFIDENCE_THRESHOLD: float = 0.30
_MAX_MISSING_FIELDS: int = 4
_MIN_EVIDENCE_COUNT: int = 1
_SAFETY_KEYWORDS: frozenset[str] = frozenset({
    "poison", "toxic", "fatality", "lethal", "chemical burn",
    "pesticide overdose", "suicidal", "emergency", "cattle death",
    "livestock death", "crop failure critical",
})


class HumanEscalationEngine:
    """
    Rule-based safety engine that determines whether an AI advisory needs
    human expert escalation before delivery to the farmer.

    The engine applies a priority-ordered chain of escalation rules and
    returns a structured escalation packet on any trigger.
    """

    def __init__(
        self,
        confidence_threshold: float = _CONFIDENCE_THRESHOLD,
        max_missing_fields: int = _MAX_MISSING_FIELDS,
        min_evidence_count: int = _MIN_EVIDENCE_COUNT,
        safety_keywords: Optional[frozenset[str]] = None,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.max_missing_fields = max_missing_fields
        self.min_evidence_count = min_evidence_count
        self.safety_keywords = safety_keywords or _SAFETY_KEYWORDS
        self._escalation_count = 0

    def _check_confidence(self, confidence: float) -> Optional[str]:
        if confidence < self.confidence_threshold:
            return (
                f"Confidence {confidence:.2%} is below safety threshold "
                f"{self.confidence_threshold:.2%}."
            )
        return None

    def _check_conflicts(self, conflicts: list[str]) -> Optional[str]:
        critical = [c for c in conflicts if "critical" in c.lower() or "unresolved" in c.lower()]
        if critical:
            return f"{len(critical)} critical unresolved conflict(s) detected."
        return None

    def _check_safety(self, query: str, warnings: list[str]) -> Optional[str]:
        combined = (query + " " + " ".join(warnings)).lower()
        triggered = [kw for kw in self.safety_keywords if kw in combined]
        if triggered:
            return f"Safety-critical keyword(s) detected: {', '.join(triggered)}."
        return None

    def _check_missing_fields(self, missing_fields: list[str]) -> Optional[str]:
        if len(missing_fields) > self.max_missing_fields:
            return (
                f"{len(missing_fields)} missing query fields exceed "
                f"escalation threshold ({self.max_missing_fields})."
            )
        return None

    def _check_evidence_count(self, evidence_count: int) -> Optional[str]:
        if evidence_count < self.min_evidence_count:
            return (
                f"Evidence count {evidence_count} is below minimum threshold "
                f"({self.min_evidence_count})."
            )
        return None

    def evaluate(
        self,
        confidence: float,
        conflicts: list[str],
        missing_fields: list[str],
        warnings: list[str],
        trace_id: str,
        query: str,
        evidence_count: int,
    ) -> tuple[bool, Optional[str], Optional[dict[str, Any]]]:
        """
        Evaluates all escalation rules.

        Returns:
          - escalated (bool): True if escalation is required.
          - reason (str | None): Human-readable escalation reason.
          - packet (dict | None): Structured escalation payload for expert routing.
        """
        # Apply rules in priority order
        reason = (
            self._check_safety(query, warnings)
            or self._check_confidence(confidence)
            or self._check_conflicts(conflicts)
            or self._check_missing_fields(missing_fields)
            or self._check_evidence_count(evidence_count)
        )

        if not reason:
            logger.debug(
                f"[EscalationEngine] No escalation triggered for trace={trace_id} "
                f"(conf={confidence:.2f})."
            )
            return (False, None, None)

        self._escalation_count += 1
        packet = self._build_packet(
            reason=reason,
            trace_id=trace_id,
            query=query,
            confidence=confidence,
            conflicts=conflicts,
            missing_fields=missing_fields,
            warnings=warnings,
        )
        logger.warning(
            f"[EscalationEngine] Escalation #{self._escalation_count} triggered "
            f"for trace={trace_id}: {reason}"
        )
        return (True, reason, packet)

    def _build_packet(
        self,
        reason: str,
        trace_id: str,
        query: str,
        confidence: float,
        conflicts: list[str],
        missing_fields: list[str],
        warnings: list[str],
    ) -> dict[str, Any]:
        """Builds a structured escalation packet for human expert routing."""
        return {
            "escalation_id": f"ESC-{self._escalation_count:05d}",
            "trace_id": trace_id,
            "timestamp": time.time(),
            "reason": reason,
            "query": query,
            "confidence": confidence,
            "conflicts": conflicts,
            "missing_fields": missing_fields,
            "warnings": warnings,
            "routing": {
                "priority": "HIGH" if confidence < 0.15 else "MEDIUM",
                "target": "KVK_EXPERT_QUEUE",
                "sla_minutes": 30 if confidence < 0.15 else 120,
            },
            "instructions": (
                "Review the above advisory and provide verified guidance to the farmer. "
                "The AI system could not reach sufficient confidence for autonomous delivery."
            ),
        }

    @property
    def escalation_count(self) -> int:
        return self._escalation_count

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "component": "HumanEscalationEngine",
            "escalations_total": self._escalation_count,
            "confidence_threshold": self.confidence_threshold,
            "max_missing_fields": self.max_missing_fields,
            "min_evidence_count": self.min_evidence_count,
        }
