# Architecture Decisions Record (ADR)

This document records the architectural design choices made during the development of the **Kisan Mitra AI** platform.

---

## ADR 01: Multi-Agent Abstraction & BaseAgent Class
* **Context**: Need a standard execution pattern across all worker agents (market, weather, soil, etc.) to guarantee integration safety.
* **Decision**: Designed an abstract `BaseAgent` parent class specifying mandatory lifecycle methods (`initialize`, `execute`, `validate`, `cleanup`, `health_check`).
* **Consequences**: Every agent can be initialized, executed, validated, and cleaned up uniformly. Allows mock agents to be swapped during testing.

## ADR 02: Swappable AI LLM Provider Factory
* **Context**: External model providers (OpenAI, Anthropic, Gemini, local Ollama) frequently update APIs. Hardcoding specific SDK calls in agents reduces flexibility.
* **Decision**: Created a unified `BaseLLMProvider` abstract model, concrete wrappers for Gemini, OpenAI, Claude, Ollama, and a registry factory class `LLMProviderFactory`.
* **Consequences**: Agents only see `BaseLLMProvider`. Providers can be swapped entirely via the `DEFAULT_LLM_PROVIDER` environment variable without changing agent prompt logic.

## ADR 03: Container Dependency Injection Pattern
* **Context**: Initializing clients, databases, caches, and registries globally pollutes memory scope, triggers circular imports, and impedes isolated unit tests.
* **Decision**: Established a dependency `Container` class instantiated on application start and attached to the FastAPI application state context.
* **Consequences**: Clear dependency chains. Avoids global variables. Makes swapping components for tests (like injecting `MockLLMProvider`) simple.

## ADR 04: Structured Domain Exceptions Hierarchy
* **Context**: Standard exceptions do not convey domain metadata and are difficult for API adapters to translate into client-friendly error envelopes.
* **Decision**: Structured a custom exceptions hierarchy extending `KisanMitraException` with properties for status codes and detail metadata maps.
* **Consequences**: Centralized error middleware can catch exceptions and automatically return formatted API responses.

## ADR 05: ContextVar-based Async Log Propagation
* **Context**: In asynchronous applications (FastAPI), thread-local log filters fail to map session and request context across coroutine boundaries.
* **Decision**: Integrated Python `contextvars` inside `logging.Filter` to dynamically load `trace_id`, `request_id`, and `session_id` into all stdout logging lines.
* **Consequences**: Logging output is instantly searchable and traceable back to the triggering transaction.

## ADR 06: Asynchronous Event Bus with Replay
* **Context**: Multi-agent communication can become tightly coupled. Need a way for agents to publish signals (like processing failures, metrics) asynchronously.
* **Decision**: Built an in-memory `EventBus` supporting publish/subscribe, history list aggregation, and replay streams.
* **Consequences**: High decoupling. System monitoring or metrics telemetry can subscribe to `*` to audit all events dynamically.

## ADR 07: Dependency Resolved DAG Scheduler
* **Context**: Some agent execution steps must run sequentially (like translation after advisory is formulated), while others can run in parallel (weather and market price checks).
* **Decision**: Developed `ExecutionScheduler` supporting sequential, parallel, and DAG graphs with dynamic topological queues using `asyncio.sleep` yields.
* **Consequences**: Prevents circular dependencies. Optimizes latency by running independent tasks concurrently.

## ADR 08: Domain Agricultural Ontology Layer
* **Context**: Agents, knowledge providers, tools, and memory layers need to communicate using a shared structured vocabulary.
* **Decision**: Designed Pydantic domain models in `backend/app/models/` for core agricultural concepts (`Crop`, `Disease`, `MarketPrice`, `GovernmentScheme`, `Farmer`).
* **Consequences**: Provides rigid type safety, JSON serialization checks, and explicit fields validation across all runtime interfaces.

## ADR 09: StateGraph-based LangGraph Orchestration Flow
* **Context**: Hand-rolling task loops and state transitions is error-prone, hard to visualize, and fails to handle conditional state chart pathways cleanly.
* **Decision**: Adopted LangGraph `StateGraph` to build a compilable execution topology connecting `Planner`, `Scheduler`, specialized worker agents, and a consolidating `Verifier`.
* **Consequences**: Clean state propagation via a shared typed dictionary. Supports granular logging on each node execution.

## ADR 10: Standardized AgentResult & UnifiedResponse Egress Contracts
* **Context**: Downstream caller API gateways need a unified structure to parse responses, metadata, latencies, and source citations.
* **Decision**: Enforced an output contract where all agents return `AgentResult`, which are consumed by `VerifierAgent` to build the final `UnifiedResponse` model.
* **Consequences**: Guarantees consistent JSON schemas, tracking metrics, and execution logs across all agent endpoints.

## ADR 11: Keyword-based Intent Engine
* **Context**: High-latency NLP/LLM parsers are excessive for simple command detection and increase call costs. Need a fast, predictable categorization engine.
* **Decision**: Constructed a dictionary-backed intent detector recognizing 14 supported intents, outputting ambiguity scores based on distance metrics.
* **Consequences**: Low latency, completely local execution, high reliability for matching commands.

## ADR 12: Rule-Based Planning Strategy Abstraction
* **Context**: Transitioning from static workflow executions to dynamic graph schedules must remain decoupled from specific AI vendor providers.
* **Decision**: Abstracted graph building behind `PlanningStrategy` and implemented `RuleBasedPlanner` returning topological steps list, dependency mappings, and parallel groups.
* **Consequences**: Easy swap-out path to introduce `LLMPlanner` or `HybridPlanner` later without modifying the orchestrator shell.

## ADR 13: Declarative Missing Information Detector
* **Context**: Worker agents need complete parameters (e.g. crop type, symptoms, location) to construct valid advice, but generating conversational prompts is complex.
* **Decision**: Developed `MissingInformationDetector` checking required entity sets based on query intents, returning validation cues without generating raw text.
* **Consequences**: Structural checks execute upstream of agent run-loops. Bypasses execution if inputs are degrade-flagged.

## ADR 14: Swappable Decision Strategy Implementations
* **Context**: The Verifier Agent uses a `DecisionEngine` that originally only supported weighted ranking. Other strategies (consensus, hybrid, and LLM-driven synthesis) were stubs that raised `NotImplementedError`.
* **Decision**: Implemented `ConsensusDecision` for majority voting, `HybridDecision` prioritizing critical/high-confidence inputs, and `FutureLLMDecision` using mock/actual LLM providers.
* **Consequences**: Verification pipeline remains decoupled from hardcoded resolution models, allowing dynamic selection of resolving strategies at runtime.

## ADR 15: Telemetry-Integrated Premium Visual Dashboard
* **Context**: The frontend initial setup was a placeholder with low aesthetic appeal and no interactivity, violating visual excellence rules.
* **Decision**: Overhauled `page.tsx` with a dark-themed visual control center showing agent nodes' health/latencies, interactive multi-agent search inputs, and structured evidence citations.
* **Consequences**: Delivers high aesthetic value, allows direct user-driven end-to-end queries, and displays full execution telemetry and warnings visually.

## ADR 16: Omnichannel Communication Core
* **Context**: Kisan Mitra AI must support a variety of communication channels (WhatsApp, Web Chat, SMS, Mobile App, IVR, Voice) with unified session timeouts, message envelope schemas, and response routers.
* **Decision**: Designed the `IChannel` interface, `MessageEnvelope`, `ResponseEnvelope` structures, and centralized `ChannelRouter`/`ResponseRouter` components.
* **Consequences**: Standardizes inbound/outbound communication flow, allows dynamic capability discovery, and isolates channel-specific quirks from the core reasoning graph.

## ADR 17: Media Intelligence Platform (MIP)
* **Context**: Ingesting raw multi-modal files (voice recordings, images, sensor logs, documents) requires standard format validation, metadata parsing, and safety scans.
* **Decision**: Built a provider-independent `IMediaProvider` abstraction registry and an execution `MediaPipeline` coordinating metadata extraction, provider dispatch, policy compliance, and channel routing.
* **Consequences**: Standardizes how agricultural media is ingested, transcribed, scanned for safety violations (via `PolicyEngine`), and routed into standard text-based envelopes.

## ADR 18: Telephony & IVR Platform
* **Context**: Need a provider-agnostic telephony and IVR menu system supporting speech queries, DTMF keypress navigation, and call session state recovery.
* **Decision**: Designed the `ITelephonyProvider` abstract adapter registry, configuration-driven `IVRStateMachine` state charts, `CallSessionManager` session lifecycle tracker, and coordinate-centric `CallManager`.
* **Consequences**: Integrates telephony as native voice/IVR channels, routing audio voicemail transcripts directly to the Media Intelligence pipeline, and handling DTMF key navigation in a decoupled, configuration-driven layout.

## ADR 19: SMS Intelligence Platform (SIP)
* **Context**: Feature phone users require highly reliable text query interfaces that are light on bandwidth but verify security parameters (spam, sensitive field leakage) and render responses using agricultural template configurations.
* **Decision**: Designed the `ISMSProvider` registry, `SMSSessionManager` thread histories, and configuration-based `SMSTemplateEngine` working in tandem with the central `SMSPipeline` coordinator.
* **Consequences**: Safely pre-processes SMS text, rate-limits spam queries, executes queries through standard message channels, and formats replies using dynamically selected templates in multiple languages (Hindi, Kannada, Telugu, Tamil, English).

## ADR 20: Registry-Driven Integration Framework
* **Context**: The platform needs to fetch weather forecasts, mandi prices, and government schemes from various external third-party systems without hardcoding specific clients or credentials.
* **Decision**: Designed a plugin-based Integration Framework with standard interfaces, a central registry, and a resilient execution wrapper (`ResilientRunner`) providing circuit breakers, retries, fallbacks, and timeouts.
* **Consequences**: Complete provider independence and elimination of vendor lock-in. Dynamic hot-swapping of active providers, stateful safety rules validation, and automated latency/failure telemetry monitoring.

## ADR 21: Production Deployment Platform & Gateway
* **Context**: Transforming Kisan Mitra AI into an enterprise-ready platform requires a secure, high-performance, and isolated multi-container architecture.
* **Decision**: Implemented:
  1. A multi-container Docker Compose stack featuring isolated networks (`kisan_network`) and persistent volumes.
  2. Secure, two-stage builder Dockerfiles executing all processes under custom non-root system users (`appuser` and `node`).
  3. An Nginx reverse proxy gateway container providing dynamic API routing, rate-limiting, security headers (CSP, HSTS), and compression.
  4. Mandatory configuration validation checks during startup that block execution if default developer credentials are used in production mode.
  5. Centralized JSON structured logging with Rotating File Handlers.
* **Consequences**: Ensures container process isolation, guards against compromised configuration launches, limits rate abuses, enables cloud observability logs routing, and passes pre-deployment audits.

## ADR 22: Reasoning Platform as the Sole Recommendation Gateway
* **Context**: Step 10C requires that no individual agent produce the final farmer recommendation independently; all worker outputs must pass through a centralized explainable reasoning layer.
* **Decision**: Route multi-agent evidence through `ChiefReasoningAgent`, which coordinates evidence collection, ranking, confidence estimation, synthesis, conflict handling, and escalation before emitting the only authoritative `ReasoningResult`.
* **Consequences**: Keeps recommendation authority centralized, preserves explainability metadata, and prevents direct worker-agent responses from bypassing governance, confidence, or escalation checks.

## ADR 23: Hierarchical Multi-Agent Reasoning with Shared Platform Components
* **Context**: Step 10C required evaluating a sequential pipeline, planner-to-independent-agents-to-aggregator, and hierarchical multi-agent reasoning. The repository already had planner, orchestration, evidence, and telemetry layers that favored extension over redesign.
* **Decision**: Adopt a hierarchical multi-agent reasoning architecture: planner/orchestrator gathers specialist evidence, `ChiefReasoningAgent` governs the reasoning stages, and shared platform components (telemetry, escalation, confidence, synthesis) are resolved from the `ReasoningPlatform` registry via DI.
* **Consequences**: Improves maintainability and startup value by reusing existing seams, strengthens explainability by keeping calibration and escalation state intact end-to-end, and avoids per-request recreation of core reasoning services.

## ADR 24: Hierarchical Multimodal Intelligence Layer
* **Context**: Step 10D required voice, image, and document understanding without duplicating the AI platform, media platform, or reasoning logic already present in the repository.
* **Decision**: Introduce a thin multimodal intelligence layer on top of the existing media and voice stacks. Media providers extract structured findings, `MultimodalEvidenceExtractor` converts them into reasoning evidence, and `ChiefReasoningAgent` remains the only path to farmer-facing recommendations.
* **Consequences**: Keeps multimodal ingestion explainable and reusable, enables voice/vision/OCR telemetry and dashboard reporting, and ensures multimodal inputs never bypass governance or reasoning controls.

## ADR 25: Shared Multimodal Telemetry and Validation
* **Context**: Step 10D introduced image quality checks, OCR requests, and speech processing that must be observable in operations without fragmenting the existing telemetry model.
* **Decision**: Extend the centralized telemetry framework with multimodal, voice, vision, and OCR metrics while adding a reusable image validation engine before CV/OCR reasoning.
* **Consequences**: Operations gains channel-specific multimodal visibility, validation failures are caught before reasoning, and the dashboard can present multimodal health using the same telemetry endpoint.

## ADR 26: Hierarchical Personalized Farmer AI Platform
* **Context**: Step 10E requires transforming Kisan Mitra AI into a personalized farming assistant capable of tracking profiles, digital twins, long-term memory, regional adaptations, and continuous learning, while strictly ensuring no personalization logic bypasses the safety controls of the central Reasoning Platform.
* **Decision**: Implemented a Hierarchical Personalization Platform that compiles farmer data into a structured `PersonalizationContext` and injects it into the `ChiefReasoningAgent` as typed `MemoryEvidence`.
* **Consequences**: Centralizes all recommendation decisions, preserves complete safety and explainability logs, supports automated scheduled calendar reminders, and updates profile preferences recursively through a feedback learning loop.




