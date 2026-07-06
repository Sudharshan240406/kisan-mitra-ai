# Architecture Overview — Kisan Mitra AI

This document details the multi-agent system architecture, planning engines, and frontend telemetry layers powering Kisan Mitra AI.

---

## 1. System Topology

Kisan Mitra AI is composed of a FastAPI microservices backend, a Next.js App Router frontend, and a multi-agent orchestration layer:

```
+-------------------------------------------------------------------+
|                           Next.js UI                              |
|   (Mission Control, Welfare Registry, Trust & Explain Center)     |
+-------------------------------------------------------------------+
                                 │ ▲ (REST APIs & WebSocket)
                                 ▼ │
+-------------------------------------------------------------------+
|                        FastAPI Backend                            |
|             (Ingress simulator, Telephony adapters)               |
+-------------------------------------------------------------------+
                                 │
                                 ▼
+-------------------------------------------------------------------+
|                     Multi-Agent Planner                           |
|       (LangGraph Router, Knowledge, Verification, Safety)        |
+-------------------------------------------------------------------+
```

---

## 2. Core Modules

### A. Digital Twin Synthesis (`app.services.demo`)
* Constructs real-time digital twins of farmer profiles, incorporating:
  * Land size (hectares), location parameters (district, state).
  * Crop lists, seasonal cultivation history, and organic registry details.
  * Direct Benefit Transfer (DBT) verification levels.

### B. Welfare Registry Rule Evaluator (`app.services.eligibility`)
* Evaluates agricultural profiles against eligibility criteria using a rule matching engine.
* Outlines reasoning chains, matches required documents list, identifies missing fields, and reports confidence metrics.

### C. Multi-Agent Orchestrator
* Routes user inputs to specialized agents:
  * **Planning Agent**: Outlines retrieval schedules.
  * **Knowledge Agent**: Pulls data from semantic indexes.
  * **Safety Agent**: Audits advice against safety guidelines.

---

## 3. Communication Channels

* **REST Endpoints**: Serves profile data, registry lists, and simulation commands.
* **WebSocket Ingress channel**: Streams real-time pipeline checkpoints (`CALL_STARTED`, `DIGITAL_TWIN_LOADED`, etc.) to drive UI highlights and timelines.
