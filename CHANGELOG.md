# Changelog

All notable changes to the **Kisan Mitra AI** project will be documented in this file.

---

## [1.0.0] - 2026-06-28
### Added
- Dedicated **pytest configurations** in `pyproject.toml` enabling out-of-the-box native async test execution and automatic module path imports.
- Robust concrete implementations for stubs in [decision.py](file:///c:/Users/Admin/Desktop/kisan-mitra-ai/backend/app/intelligence/decision.py) (`ConsensusDecision`, `HybridDecision`, and `FutureLLMDecision`) to prevent NotImplementedError crashes and provide production-ready fallback logic.
- A **premium, responsive agricultural dashboard** in `frontend/app/page.tsx` leveraging Tailwind CSS, Lucide icons, and modern telemetry components for visualizing trust thresholds, confidence ratings, warnings, evidence, logs, and multi-agent health states.
- Automated browser E2E test verification recording.

## [0.5.0] - 2026-06-28
### Added
- Rule-based **Intent Engine** supporting 14 agricultural intents (Weather, Disease, Market, etc.) and returning structured `IntentResult`.
- **Entity Extraction** framework matching crop, disease, locations, seasons, schemes, and languages using standard ontology models.
- **Missing Information Detector** and report structures flagging data gaps (missing crop type, weather location, symptoms, commodity name).
- **Query Analysis** unified context wrapper consolidating raw/normalized strings, intents, entities, ambiguities, and missing fields.
- Abstract `PlanningStrategy` interface and concrete `RuleBasedPlanner` mapping intents/entities into topological `ExecutionPlan` task graphs.
- **Workflow Engine** and templates registry managing template steps list.
- Standard unit test cases (`test_intelligence.py`) covering intent scores, entity lookups, missing reports, registry discover hooks, and planner graphs.
- Dynamic route planning mapping in `AgentOrchestrator` feeding computed planner steps into the LangGraph state machine.

## [0.4.0] - 2026-06-28
### Added
- Standardized Agricultural Ontology Layer Pydantic models under `backend/app/models/` (`Crop`, `Disease`, `MarketPrice`, `GovernmentScheme`, `Farmer`).
- Unified response interfaces (`AgentResult` and `UnifiedResponse` schemas in `responses.py`).
- Abstract Memory Layer interfaces under `backend/app/core/memory.py` (`SessionMemory`, `ConversationMemory`, `FarmerMemory`, `LongTermMemory`).
- Extended `KnowledgeProvider` with specialized subclasses (`ChromaDBKnowledgeProvider`, `GovDocsKnowledgeProvider`, `ManualsKnowledgeProvider`, `ResearchPapersKnowledgeProvider`, `MarketBulletinsKnowledgeProvider`, `WeatherKnowledgeProvider`).
- Core agent skeletons (`WeatherAgent`, `MarketAgent`, `MemoryAgent`, `KnowledgeAgent`, `GovernmentSchemeAgent`, `VerifierAgent`) inheriting from `BaseAgent`.
- Concrete tool skeletons under `backend/app/tools/` (`WeatherTool`, `MarketTool`, `KnowledgeTool`, `MemoryTool`, `GovernmentSchemeTool`) inheriting from `BaseTool`.
- StateGraph-based LangGraph orchestration workflow compiler in `backend/app/orchestrator/graph.py` linking Planner, Scheduler, worker agents, and Verifier.
- Lifecycle auto-registration in `main.py` for all new agent skeletons.

## [0.3.0] - 2026-06-28
### Added
- Standardized `AgentContext` and `AgentState` models for context and metrics tracking.
- Context-propagating asynchronous logger filter using Python `contextvars` to bind trace keys to logs automatically.
- Asynchronous-ready `EventBus` with wildcard tracking subscriptions (`*`), event histories, and replay logs.
- Dynamic `ExecutionScheduler` supporting sequential steps, concurrent parallel gathers, and dependency-resolved Directed Acyclic Graphs (DAG).
- Abstract `BaseTool` class for third-party client integrations.
- Abstract `KnowledgeProvider` class for semantic RAG databases (ChromaDB, PDF manual indexing).
- Centralized `RuntimeManager` for coordinating agent startup/shutdown lifecycles and context propagation.
- Telemetry `MetricsCollector` tracing execution latency, token usage, tool invocations, retries, and errors.
- Broad health check capability in `/health` query paths reporting stats for registry, event bus, scheduler, and metrics.

## [0.2.0] - 2026-06-28
### Added
- Abstract `BaseAgent` class with standard lifecycles and logging decorators.
- Centralized `AgentRegistry` for worker and planner agent registration and discovery.
- Dependency Injection `Container` pattern and FastAPI state binder.
- Swappable LLM Provider abstractions (`BaseLLMProvider` with Mock, Gemini, OpenAI, Claude, Ollama support).
- Core exceptions tree (`KisanMitraException`, `AgentException`, etc.).
- Standardized request and response schemas (Pydantic model parameters).
- General utilities (`id.py`, `time.py`, `validation.py`, `constants.py`).

## [0.1.0] - 2026-06-28
### Added
- Next.js 14+ frontend project initialization with Tailwind CSS and shadcn/ui.
- FastAPI backend project initialization with startup lifespan and logging.
- Docker Compose configuration for PostgreSQL, Redis, ChromaDB, backend, and frontend.
- Repository configuration files (`.gitignore`, `LICENSE` Apache 2.0, `.env.example`).
- GitHub workflow CI lint pipeline configuration.
- Ruff, Black, isort, mypy configuration file (`pyproject.toml`).
