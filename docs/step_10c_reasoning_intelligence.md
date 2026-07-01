# Step 10C: AI Reasoning & Decision Intelligence

## Engineering Brief

Step 10C extends the existing orchestrator into an explainable reasoning platform without rebuilding completed subsystems. The implementation keeps worker agents focused on evidence generation while making `ChiefReasoningAgent` the only component allowed to emit farmer-facing recommendations.

## Repository Intelligence Report

- `backend/app/orchestrator/graph.py` already routes agent outputs into a dedicated reasoning node.
- `backend/app/reasoning/` already contains the Step 10C core modules: evidence, confidence, consensus, synthesis, escalation, telemetry, and chief-agent coordination.
- `backend/app/core/container.py` is the repository's DI seam, so Step 10C runtime wiring belongs there.
- `backend/app/voice/reasoning.py` is the voice-channel bridge and must reuse the same reasoning contract rather than introducing a parallel advisory flow.

## Tree Of Thoughts

### Option A: Sequential Pipeline
- Maintainability: simple but brittle as stages grow.
- Explainability: acceptable, but weak for alternatives and conflict review.
- Performance: predictable, but every step runs even when unnecessary.
- Cost: moderate.
- Scalability: limited.
- Startup Value: quick to ship.
- Human Trust: moderate.

### Option B: Planner -> Independent Agents -> Aggregator
- Maintainability: good reuse of existing planner/worker split.
- Explainability: better than A, but the aggregator becomes a hidden bottleneck if it does not own escalation and calibration.
- Performance: good.
- Cost: good.
- Scalability: good.
- Startup Value: strong.
- Human Trust: good.

### Option C: Hierarchical Multi-Agent Reasoning
- Maintainability: strongest fit with the existing repository because it layers on current orchestrator, DI, telemetry, and governance seams.
- Explainability: strongest because evidence ranking, confidence, conflicts, and escalation stay centralized.
- Performance: slightly more coordination overhead, but still efficient with shared components.
- Cost: slightly higher than A, offset by fewer unsafe outputs.
- Scalability: high.
- Startup Value: strong because it reuses completed systems.
- Human Trust: strongest.

Selected architecture: Option C.

## Implementation Notes

- Preserved escalation state through session finalization instead of overwriting it as `completed`.
- Promoted reasoning telemetry to a shared DI-managed component instead of recreating it per request.
- Propagated calibration flags and confidence intervals from the confidence engine into downstream safety metadata.
- Added evidence-count escalation support to match the Step 10C safety brief.
- Repaired the voice reasoning bridge so it calls `ChiefReasoningAgent.reason(...)` with the live contract.

## Verification Summary

- `pytest tests/test_reasoning_platform.py -q`
- `pytest tests/test_voice_reasoning.py -q`

Additional note: broader suites that import `Settings` were previously failing in this environment because `DEBUG=release` was not boolean-parseable; Step 10C now normalizes that value safely.
