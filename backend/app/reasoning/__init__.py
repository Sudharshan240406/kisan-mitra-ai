"""
Kisan Mitra AI — Reasoning Package
=====================================
AI Reasoning & Decision Intelligence Platform.

Package exposes the public API surface of the reasoning layer:
  - ReasoningPlatform: bootstrap / lifecycle container
  - ReasoningContext: session-scoped request context
  - ChiefReasoningAgent + ReasoningResult: coordination & output
  - EvidenceCollector, EvidenceRankingEngine, RankedEvidence: evidence layer
  - ConfidenceEngine, ConfidenceReport: confidence estimation
  - ConsensusEngine, ConflictResolutionEngine: agreement & conflict resolution
  - DecisionSynthesizer, ExplainabilityEngine: synthesis & XAI
  - HumanEscalationEngine: safety escalation
  - ReasoningTelemetry: observability
"""

from app.reasoning.chief import ChiefReasoningAgent, ReasoningResult
from app.reasoning.confidence import ConfidenceEngine, ConfidenceReport
from app.reasoning.consensus import ConflictResolutionEngine, ConsensusEngine
from app.reasoning.core import ReasoningContext, ReasoningMetrics, ReasoningPlatform, ReasoningSession
from app.reasoning.escalation import HumanEscalationEngine
from app.reasoning.evidence import EvidenceCollector, EvidenceRankingEngine, RankedEvidence
from app.reasoning.synthesis import DecisionSynthesizer, ExplainabilityEngine
from app.reasoning.telemetry import ReasoningTelemetry

__all__ = [
    # Core
    "ReasoningPlatform",
    "ReasoningContext",
    "ReasoningSession",
    "ReasoningMetrics",
    # Chief Agent
    "ChiefReasoningAgent",
    "ReasoningResult",
    # Evidence
    "EvidenceCollector",
    "EvidenceRankingEngine",
    "RankedEvidence",
    # Confidence
    "ConfidenceEngine",
    "ConfidenceReport",
    # Consensus
    "ConsensusEngine",
    "ConflictResolutionEngine",
    # Synthesis & XAI
    "DecisionSynthesizer",
    "ExplainabilityEngine",
    # Escalation
    "HumanEscalationEngine",
    # Telemetry
    "ReasoningTelemetry",
]
