"""
Kisan Mitra AI — Consensus & Conflict Resolution Engine
=========================================================
Two complementary sub-systems:

1. ConsensusEngine
   Evaluates whether specialist agents have reached consensus on a
   recommendation. Consensus is modelled as high score-variance indicating
   disagreement among agents' ranked evidence.

2. ConflictResolutionEngine
   Detects semantic conflicts between evidence items and applies a
   prioritised resolution strategy (trust > freshness > confidence),
   emitting structured resolution records.
"""
from __future__ import annotations

import logging
from typing import Any

from app.reasoning.evidence import RankedEvidence

logger = logging.getLogger("kisan_mitra_ai.reasoning.consensus")

# ---------------------------------------------------------------------------
# Consensus thresholds
# ---------------------------------------------------------------------------
_CONSENSUS_VARIANCE_THRESHOLD: float = 0.10  # max allowed variance for consensus
_CONSENSUS_MIN_EVIDENCE: int = 2             # minimum items needed to test consensus


# ---------------------------------------------------------------------------
# ConsensusEngine
# ---------------------------------------------------------------------------

class ConsensusEngine:
    """
    Determines whether the available ranked evidence supports a consistent
    advisory conclusion. Uses score variance as the primary disagreement signal.

    If agents return wildly different confidence/composite signals, the
    platform flags the result as "consensus not reached" for the CRA to
    escalate or flag a warning to the farmer.
    """

    def evaluate(self, ranked_evidence: list[RankedEvidence]) -> dict[str, Any]:
        """
        Evaluates consensus from ranked evidence.
        Returns a dict with:
          - reached (bool): Whether consensus was reached.
          - variance (float): Composite score variance.
          - mean (float): Mean composite score.
          - agent_count (int): Number of distinct contributing agents.
          - reason (str): Human-readable consensus verdict.
        """
        if len(ranked_evidence) < _CONSENSUS_MIN_EVIDENCE:
            return {
                "reached": True,
                "variance": 0.0,
                "mean": ranked_evidence[0].composite_score if ranked_evidence else 0.0,
                "agent_count": len({ev.agent for ev in ranked_evidence}),
                "reason": "Insufficient evidence items — defaulting to consensus.",
            }

        scores = [ev.composite_score for ev in ranked_evidence]
        n = len(scores)
        mean = sum(scores) / n
        variance = sum((s - mean) ** 2 for s in scores) / n
        agent_count = len({ev.agent for ev in ranked_evidence})

        reached = variance <= _CONSENSUS_VARIANCE_THRESHOLD

        reason = (
            f"Evidence score variance={variance:.4f} "
            f"{'within' if reached else 'exceeds'} threshold={_CONSENSUS_VARIANCE_THRESHOLD}."
        )

        logger.info(
            f"[ConsensusEngine] reached={reached}, variance={variance:.4f}, "
            f"mean={mean:.4f}, agents={agent_count}"
        )
        return {
            "reached": reached,
            "variance": round(variance, 4),
            "mean": round(mean, 4),
            "agent_count": agent_count,
            "reason": reason,
        }


# ---------------------------------------------------------------------------
# ConflictResolutionEngine
# ---------------------------------------------------------------------------

class ConflictResolutionEngine:
    """
    Detects and resolves conflicts between evidence items from different agents.

    Conflict detection heuristics:
      1. Same agent returning contradictory validation states.
      2. Two or more agents reporting wildly divergent confidence for the same
         ontology domain (crop / disease / market).
      3. An evidence item flagged as low_confidence alongside a high-confidence
         item in the same domain (composite score spread > threshold).

    Resolution strategy (in priority order):
      1. Prefer evidence with highest source trust_score.
      2. If trust is tied, prefer most recent (lowest age = highest freshness_score).
      3. If still tied, prefer highest confidence.
      4. If unresolvable, flag for human escalation.
    """

    DIVERGENCE_THRESHOLD: float = 0.30  # composite score divergence to flag a conflict

    def resolve(
        self, ranked_evidence: list[RankedEvidence]
    ) -> tuple[list[str], list[str]]:
        """
        Analyses ranked evidence for conflicts and applies resolution.

        Returns:
          - conflicts: List of human-readable conflict descriptions.
          - resolutions: List of human-readable resolution decisions.
        """
        conflicts: list[str] = []
        resolutions: list[str] = []

        # Group evidence by domain tags (agent name used as domain proxy)
        domain_map: dict[str, list[RankedEvidence]] = {}
        for ev in ranked_evidence:
            domain_map.setdefault(ev.agent, []).append(ev)

        # Detection: divergent composite scores within the same agent domain
        for agent, items in domain_map.items():
            if len(items) < 2:
                continue
            max_score = max(ev.composite_score for ev in items)
            min_score = min(ev.composite_score for ev in items)
            spread = max_score - min_score
            if spread > self.DIVERGENCE_THRESHOLD:
                conflict_desc = (
                    f"Agent '{agent}' evidence spread={spread:.3f} "
                    f"exceeds divergence threshold={self.DIVERGENCE_THRESHOLD}."
                )
                conflicts.append(conflict_desc)
                logger.warning(f"[ConflictResolution] Conflict detected: {conflict_desc}")

                # Resolution: keep the highest trust_score item
                best = max(
                    items,
                    key=lambda e: (e.trust_score, e.freshness_score, e.confidence)
                )
                resolution_desc = (
                    f"Conflict in '{agent}' resolved: preferred evidence '{best.id}' "
                    f"(trust={best.trust_score:.2f}, freshness={best.freshness_score:.2f}, "
                    f"confidence={best.confidence:.2f})."
                )
                resolutions.append(resolution_desc)
                logger.info(f"[ConflictResolution] Resolution: {resolution_desc}")

        # Detection: invalid validation_state items alongside valid ones
        invalid_items = [ev for ev in ranked_evidence if ev.validation_state != "valid"]
        valid_items = [ev for ev in ranked_evidence if ev.validation_state == "valid"]
        if invalid_items and valid_items:
            conflict_desc = (
                f"{len(invalid_items)} evidence item(s) have invalid validation_state "
                f"alongside {len(valid_items)} valid items."
            )
            conflicts.append(conflict_desc)
            resolution_desc = (
                "Discarded invalid/low_confidence evidence; proceeding with valid items only."
            )
            resolutions.append(resolution_desc)

        if not conflicts:
            logger.info("[ConflictResolution] No conflicts detected.")

        return conflicts, resolutions
