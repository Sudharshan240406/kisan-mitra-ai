# Kisan Mitra AI — System Architecture & API Details

This document details the software architecture, agent topology, and registered API routes of Kisan Mitra AI.

---

## 1. System Architecture Details

```
                          ┌────────────────────────┐
                          │    Next.js Frontend    │ (Turbopack, TypeScript)
                          └───────────┬────────────┘
                                      │
                 ┌────────────────────┴────────────────────┐
                 │ (REST / JSON)                           │ (WebSocket Events)
                 ▼                                         ▼
   ┌───────────────────────────┐             ┌───────────────────────────┐
   │  FastAPI REST Endpoints   │             │   FastAPI WebSockets      │
   │ (65 routes total)         │             │  (ws://localhost:8000)    │
   └─────────────┬─────────────┘             └─────────────┬─────────────┘
                 │                                         │
                 ├────────────────────┬────────────────────┤
                 │                    │                    │
                 ▼                    ▼                    ▼
   ┌───────────────────────────┐┌───────────┐┌───────────────────────────┐
   │  Agent Orchestrator Graph ││ PostgreSQL││    Chroma Vector DB       │
   │ (7 specialized AI agents) ││ (Digital) ││  (Agricultural Knowledge) │
   └─────────────┬─────────────┘└───────────┘└───────────────────────────┘
                 │
                 ▼
   ┌───────────────────────────┐
   │    Eligibility Engine     │
   │ (11 rule-based schemes)   │
   └───────────────────────────┘
```

- **Next.js Frontend**: Consumes JSON APIs for static setups and connects to the WebSocket endpoint for call tracking.
- **FastAPI Backend**: Registers routes and delegates long-running workflows to the multi-agent graph or eligibility engine.
- **Agent Orchestrator Graph**: Routes tasks semantically to the target specialist agent (Weather, Mandi Market, Government Schemes, etc.).
- **ChromaDB**: Holds vector embeddings of agricultural manuals and scheme guidelines to enable semantic context retrieval.
- **Eligibility Engine**: A high-efficiency evaluator that determines scheme compliance.

---

## 2. API Endpoint Inventory (FastAPI)

Below is a categorized summary of key endpoints among the 65 registered routes:

### Demo & Simulation (`/api/v1/demo`)
- `GET  /farmers` — List all 6 demo farmer profiles
- `GET  /farmers/{id}` — Get a specific farmer profile
- `GET  /schemes/{id}` — Run bulk eligibility and return raw JSON verdict
- `POST /simulate-call/{id}` — Trigger the E2E simulation pipeline
- `POST /start` — Execute sequentially through all 6 demo farmers
- `GET  /status` — Get demo mode active settings and statistics

### Telephony (`/api/v1/telephony`)
- `POST /incoming` — Handle incoming voice calls from carriers
- `POST /dtmf` — Consume caller digit inputs and process transitions
- `POST /voice/webhook` — Entrypoint for Twilio/Exotel Webhooks

### Health & Telemetry (`/api/v1/health`, `/api/v1/telemetry`)
- `GET  /health` — Complete system status and database connect checks
- `GET  /telemetry/metrics` — Export operations metrics (total calls, success rates)

### AI Advisory (`/api/v1/ai`, `/api/v1/query`)
- `POST /query` — Single REST endpoint to execute ad-hoc questions through the orchestrator
- `GET  /ai/agents` — List health of registered specialist agents
- `POST /ai/diagnose` — Sandbox route to test prompts against specific agents
