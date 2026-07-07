# Learning & Feedback Engine

The **Learning & Feedback Engine** enables Kisan Mitra AI to continuously improve recommendation performance, confidence ratings, regional and language suitability, and document citations utility over time by tracking farmer actions and specialist agent execution telemetry.

---

## Directory & Package Structure

The engine code is organized under `backend/app/learning/`:

```
backend/app/learning/
├── __init__.py                  # Package exports
├── feedback_store.py            # Pydantic schemas and JSON file persistence layer
├── feedback_engine.py           # Logging and registry helper class
├── confidence_optimizer.py      # Dynamic rating tuning and offsets adjustments
├── recommendation_optimizer.py  # Scheme/advice/regional/language weights optimizer
├── ranking_engine.py            # Reranks recommendations based on preference weights
└── learning_manager.py          # Central coordinator and analytics reporting API
```

---

## Data Models (Schemas)

Located in [feedback_store.py](file:///c:/Users/Admin/Desktop/kisan-mitra-ai/backend/app/learning/feedback_store.py):

1. **`RecommendationFeedback`**
   - Tracks whether a suggestion was `accepted`, `rejected`, or `ignored`.
   - Records optional `manual_correction` texts.
   - Includes regional, language, scheme, and crop metadata.

2. **`KnowledgeFeedback`**
   - Tracks document utility actions: `'cited'`, `'useful'`, `'ignored'`, or `'low_quality'`.

3. **`AgentFeedback`**
   - Records execution latency (ms), retry counts, and success status of specialized agents.

---

## Algorithms and Optimization Engines

### 1. Confidence Optimizer
Adjusts the baseline confidence levels dynamically using historical outcomes:
- **Tuning Step**: When a crop-region recommendation is accepted, the offset is boosted by `+0.02`. When rejected, it is penalized by `-0.05` (bounded between `[-0.20, +0.20]`).
- **Tuning Formula**:
  $$\text{Confidence}_{\text{opt}} = \text{Confidence}_{\text{base}} + \text{Offset}_{\text{crop}} + \text{Offset}_{\text{region}}$$

### 2. Recommendation Optimizer & Ranking Engine
Learns farmer cohort preferences (crop, region, language, and welfare schemes):
- Adjusts weights on recommendation acceptance/rejection.
- Reranks and sorts candidate recommendations based on learned preference score boosts.

---

## Orchestrator Integration

### Agent Execution Telemetry
The [AgentOrchestrator](file:///c:/Users/Admin/Desktop/kisan-mitra-ai/backend/app/orchestrator/orchestrator.py) wraps specialist agent execution, automatically recording latency and success rates to the `FeedbackStore`.

### Knowledge Utility Tracking
Compares documents retrieved by the knowledge engine against the final evidence list used by the Chief Reasoning Agent:
- If a document is in `evidence_used`, it is logged as `"cited"` (or `"useful"` if recommendation accepted).
- If it is omitted, it is logged as `"ignored"`.
- If its quality score is low (< 0.5), it is flagged as `"low_quality"`.

---

## REST API Endpoints

Exposed in [personalization.py](file:///c:/Users/Admin/Desktop/kisan-mitra-ai/backend/app/api/v1/personalization.py):

* **POST** `/api/v1/personalization/memory/feedback`
  - Submits farmer ratings and feedback.
  - Automatically invokes the new `LearningManager` to adjust confidence offsets and cohort weights.
* **GET** `/api/v1/personalization/learning/analytics`
  - Returns analytics including overall acceptance rate, recommendation quality index, confidence evolution, and top preferred categories/schemes.
