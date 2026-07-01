"""
Kisan Mitra AI — Reasoning Platform Core
=========================================
Implements the core infrastructure for the AI Reasoning & Decision Intelligence
Platform. This module provides the foundational data models, registry, caching,
session management, metrics collection, and bootstrapping entry point.

Architecture: Hierarchical Multi-Agent Reasoning System (ADR-23)
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.reasoning.core")


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class ReasoningContext(BaseModel):
    """
    Runtime variables propagated through an active reasoning session.
    Carries the original request, session trace, agent execution plan,
    and intermediate state accumulations.
    """
    session_id: str = Field(..., description="Unique reasoning session identifier.")
    trace_id: str = Field(..., description="Distributed tracing identifier for log correlation.")
    request_id: str = Field(..., description="Request identifier for this advisory evaluation.")
    query: str = Field(..., description="Original farmer query under evaluation.")
    language: str = Field(default="en", description="Target ISO language for advisory output.")
    crop: Optional[str] = Field(default=None, description="Primary crop context.")
    location: Optional[str] = Field(default=None, description="Farmer location context.")
    farmer_id: Optional[str] = Field(default=None, description="Farmer profile identifier.")
    agent_plan: list[str] = Field(default_factory=list, description="Planned specialist agent execution order.")
    agent_outputs: dict[str, Any] = Field(default_factory=dict, description="Collected raw agent output by name.")
    missing_fields: list[str] = Field(default_factory=list, description="Fields absent from the original query.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary context extensions.")


class ReasoningSession(BaseModel):
    """
    Container for a complete reasoning session lifecycle.
    Records start, end, status, and intermediate stage timestamps.
    """
    session_id: str = Field(..., description="Unique session identifier.")
    trace_id: str = Field(..., description="Associated trace identifier.")
    start_time: float = Field(default_factory=time.time, description="Session start timestamp.")
    end_time: Optional[float] = Field(default=None, description="Session end timestamp.")
    status: str = Field(default="running", description="Session status: running | completed | failed | escalated.")
    stages_completed: list[str] = Field(default_factory=list, description="Ordered list of completed reasoning stages.")
    escalated: bool = Field(default=False, description="Whether human escalation was triggered.")
    confidence: Optional[float] = Field(default=None, description="Final overall confidence estimate.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible session metadata.")

    def complete(self, confidence: float) -> None:
        self.end_time = time.time()
        self.status = "completed"
        self.confidence = confidence

    def fail(self, reason: str) -> None:
        self.end_time = time.time()
        self.status = "failed"
        self.metadata["failure_reason"] = reason

    def escalate(self) -> None:
        self.end_time = time.time()
        self.status = "escalated"
        self.escalated = True

    @property
    def duration_ms(self) -> float:
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000.0


class ReasoningMetrics(BaseModel):
    """
    Accumulates performance counters for a reasoning session.
    Published to the Event Bus on session completion.
    """
    total_sessions: int = 0
    completed_sessions: int = 0
    failed_sessions: int = 0
    escalated_sessions: int = 0
    avg_duration_ms: float = 0.0
    avg_confidence: float = 0.0
    avg_evidence_count: float = 0.0
    consensus_success_rate: float = 0.0
    conflict_resolution_count: int = 0
    _durations: list[float] = []
    _confidences: list[float] = []
    _evidence_counts: list[int] = []
    _consensus_results: list[bool] = []

    model_config = {"arbitrary_types_allowed": True}

    def record_session(
        self,
        session: ReasoningSession,
        confidence: float,
        evidence_count: int,
        consensus_success: bool
    ) -> None:
        self.total_sessions += 1
        if session.status == "completed":
            self.completed_sessions += 1
        elif session.status == "failed":
            self.failed_sessions += 1
        elif session.status == "escalated":
            self.escalated_sessions += 1

        self._durations.append(session.duration_ms)
        self._confidences.append(confidence)
        self._evidence_counts.append(evidence_count)
        self._consensus_results.append(consensus_success)

        if session.escalated:
            self.escalated_sessions = max(self.escalated_sessions, 1)

        n = len(self._durations)
        self.avg_duration_ms = sum(self._durations) / n
        self.avg_confidence = sum(self._confidences) / n
        self.avg_evidence_count = sum(self._evidence_counts) / n
        self.consensus_success_rate = sum(1 for r in self._consensus_results if r) / n
        if session.escalated:
            self.conflict_resolution_count += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_sessions": self.total_sessions,
            "completed_sessions": self.completed_sessions,
            "failed_sessions": self.failed_sessions,
            "escalated_sessions": self.escalated_sessions,
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "avg_confidence": round(self.avg_confidence, 3),
            "avg_evidence_count": round(self.avg_evidence_count, 1),
            "consensus_success_rate": round(self.consensus_success_rate, 3),
            "conflict_resolution_count": self.conflict_resolution_count,
        }


class ReasoningCache:
    """
    LRU-style in-memory cache for reasoning outcomes indexed by query hash.
    Prevents redundant re-evaluation for identical or near-identical queries.
    """
    def __init__(self, max_size: int = 512, ttl_seconds: float = 300.0) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._hits = 0
        self._misses = 0

    def _key(self, query: str, language: str) -> str:
        return f"{language}::{query.lower().strip()}"

    def get(self, query: str, language: str = "en") -> Optional[Any]:
        key = self._key(query, language)
        entry = self._store.get(key)
        if entry:
            value, ts = entry
            if (time.time() - ts) <= self.ttl_seconds:
                self._hits += 1
                return value
            del self._store[key]
        self._misses += 1
        return None

    def set(self, query: str, value: Any, language: str = "en") -> None:
        key = self._key(query, language)
        if len(self._store) >= self.max_size:
            oldest = min(self._store, key=lambda k: self._store[k][1])
            del self._store[oldest]
        self._store[key] = (value, time.time())

    @property
    def stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        return {
            "size": len(self._store),
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": round(self._hits / total, 3) if total > 0 else 0.0,
        }


class ReasoningRegistry:
    """
    Registry of named reasoning components (engines, strategies, resolvers).
    Enables modular, plug-in driven upgrades of individual reasoning sub-systems.
    """
    def __init__(self) -> None:
        self._components: dict[str, Any] = {}

    def register(self, name: str, component: Any) -> None:
        self._components[name] = component
        logger.info(f"[ReasoningRegistry] Registered component: '{name}'")

    def get(self, name: str) -> Any:
        component = self._components.get(name)
        if component is None:
            raise KeyError(f"[ReasoningRegistry] Component '{name}' not found.")
        return component

    def list_components(self) -> list[str]:
        return list(self._components.keys())


class ReasoningPlatform:
    """
    Unified bootstrap entry point for the AI Reasoning & Decision Intelligence
    Platform. Initializes and holds references to all reasoning sub-systems,
    orchestrates session lifecycle management, and publishes telemetry events.
    """
    def __init__(self) -> None:
        self.registry = ReasoningRegistry()
        self.cache = ReasoningCache()
        self.metrics = ReasoningMetrics()
        self._active_sessions: dict[str, ReasoningSession] = {}
        logger.info("[ReasoningPlatform] AI Reasoning & Decision Intelligence Platform bootstrapped.")

    def create_session(self, trace_id: str, query: str) -> ReasoningSession:
        """Creates and tracks a new reasoning session."""
        session_id = f"RSN-{uuid.uuid4().hex[:8].upper()}"
        session = ReasoningSession(session_id=session_id, trace_id=trace_id)
        self._active_sessions[session_id] = session
        logger.info(f"[ReasoningPlatform] Session created: {session_id} (trace={trace_id})")
        return session

    def get_session(self, session_id: str) -> Optional[ReasoningSession]:
        return self._active_sessions.get(session_id)

    def complete_session(
        self,
        session: ReasoningSession,
        confidence: float,
        evidence_count: int,
        consensus_success: bool
    ) -> None:
        if session.status == "running":
            session.complete(confidence)
        else:
            session.confidence = confidence
            if session.end_time is None:
                session.end_time = time.time()
        self.metrics.record_session(session, confidence, evidence_count, consensus_success)
        logger.info(
            f"[ReasoningPlatform] Session {session.session_id} completed. "
            f"Status={session.status}, Confidence={confidence:.2f}, Duration={session.duration_ms:.1f}ms"
        )

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "active_sessions": len(self._active_sessions),
            "registered_components": self.registry.list_components(),
            "cache_stats": self.cache.stats,
            "metrics": self.metrics.to_dict(),
        }
