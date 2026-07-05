# Kisan Mitra AI — System Architecture & Software Design Document

This document provides a technical walkthrough of the Kisan Mitra AI codebase architecture, database models, multi-agent coordination pipelines, and software design diagrams.

---

## 1. System Component Diagram

The following diagram maps the software boundaries, API endpoints, and structural dependencies:

```mermaid
graph TD
    classDef client fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef backend fill:#0f172a,stroke:#10b981,stroke-width:2px,color:#f8fafc;
    classDef storage fill:#0f172a,stroke:#a855f7,stroke-width:2px,color:#f8fafc;
    classDef agent fill:#0f172a,stroke:#f59e0b,stroke-width:2px,color:#f8fafc;

    subgraph UserInterface["Client Tier"]
        Dashboard["Mission Control SPA (Next.js)"]:::client
        PhoneClient["Farmer Mobile / Telephony handset"]:::client
    end

    subgraph ServiceContainer["FastAPI Backend Container"]
        MainRouter["FastAPI Application (main.py)"]:::backend
        WSManager["WebSocket Connection Manager"]:::backend
        TelephonyManager["Call Session Manager"]:::backend
        
        subgraph LogicEngine["Core Intelligence Services"]
            EligEngine["Eligibility Engine (EligibilityEngine)"]:::backend
            DocAdvisor["Document Advisor (DocumentAdvisor)"]:::backend
            DemoService["Demo Service (DemoService)"]:::backend
        end
        
        subgraph AgentRegistry["Multi-Agent Graph Orchestrator"]
            Planner["Planner Agent (Central Router)"]:::agent
            GovScheme["Government Scheme Specialist"]:::agent
            WeatherSpec["Weather Specialist"]:::agent
            MarketSpec["Market Mandi Specialist"]:::agent
        end
    end

    subgraph Databases["Persistence Tier"]
        Postgres["PostgreSQL DB (Farmer Profiles)"]:::storage
        Redis["Redis (Active Session Cache)"]:::storage
        Chroma["Chroma Vector DB (Advisory Embeddings)"]:::storage
    end

    %% Client Mappings
    PhoneClient -->|SIP / RTP Inbound| TelephonyManager
    Dashboard -->|WebSocket Live Stream| WSManager
    Dashboard -->|REST JSON APIs| MainRouter

    %% Routing Mappings
    MainRouter --> WSManager
    TelephonyManager -->|Read / Write CallSession| Redis
    TelephonyManager -->|Delegate DTMF| EligEngine
    EligEngine -->|Evaluate All Rules| GovScheme
    EligEngine -->|Resolve Profile| Postgres
    GovScheme -->|Query Embeddings| Chroma
    
    %% Service Output Mappings
    EligEngine --> DocAdvisor
    DocAdvisor -->|Voice Summary Output| MainRouter
```

---

## 2. Database Entity-Relationship (ER) Diagram

The following diagram maps the database entity properties, primary/foreign keys, and model relations:

```mermaid
erDiagram
    FARMER ||--o{ CALL_SESSION : initiates
    FARMER {
        string farmer_id PK
        string name
        string phone_number UK
        string state
        string district
        string category
        string gender
        double land_size_hectares
        string active_crops
        boolean has_bank_account
        boolean has_aadhaar
        boolean is_organic
        boolean is_tenant
        string preferred_language
    }
    
    CALL_SESSION ||--o{ SCHEME_RECOMMENDATION : produces
    CALL_SESSION {
        string call_id PK
        string farmer_id FK
        string current_ivr_state
        string language
        double start_timestamp
        double last_activity
        string call_metadata
    }

    SCHEME_RECOMMENDATION {
        string recommendation_id PK
        string call_id FK
        string scheme_id
        string status
        double confidence
        string reasoning
        string evidence
        string required_documents
        string application_steps
    }
```

---

## 3. End-to-End Execution Sequence Diagram

The following sequence map traces a caller's request, detailing the workflow stages and WebSocket update dispatches:

```mermaid
sequenceDiagram
    autonumber
    actor Farmer as 👨‍🌾 Farmer Handset
    participant Carrier as ☎ Telephony Carrier
    participant CallMgr as ⚙ Call Session Manager
    participant Twin as 👤 Digital Twin Service
    participant Engine as 🏛 Eligibility Engine
    participant Agent as 🧠 Chief Reasoning Agent
    participant Advisor as 📄 Document Advisor
    participant WS as ⚡ WebSocket Stream
    actor Dashboard as 🖥 Operations Dashboard

    %% Phase 1: Onboarding
    Farmer->>Carrier: Dial Advisory Number
    Carrier->>CallMgr: Inbound SIP Call Event
    CallMgr->>WS: Broadcast [CALL_STARTED]
    WS-->>Dashboard: Animate Canvas State
    CallMgr->>WS: Broadcast [CALLER_IDENTIFIED]
    CallMgr->>Twin: Resolve Phone Registry
    Twin->>WS: Broadcast [DIGITAL_TWIN_LOADED]
    WS-->>Dashboard: Populate Farmer Profile & Digital Twin details

    %% Phase 2: Intent & Evaluation
    Farmer->>Carrier: Press 1 (Government Schemes Intent)
    Carrier->>CallMgr: HTTP POST Webhook (digits=1)
    CallMgr->>WS: Broadcast [SCHEME_SEARCH_STARTED]
    CallMgr->>Engine: Run Scheme Eligibility Engine
    
    loop Match 11 Government Schemes
        Engine->>Engine: Match Farmer attributes vs Scheme rules
        Engine->>WS: Broadcast [SCHEME_MATCHED] (one by one)
        WS-->>Dashboard: Progressive match cards slide in
    end
    
    Engine->>CallMgr: Compile Verdict List
    CallMgr->>WS: Broadcast [ELIGIBILITY_COMPLETED]
    
    %% Phase 3: Reasoning & Advice
    CallMgr->>Agent: Run Chief Reasoning Synthesis
    Agent->>WS: Broadcast [REASONING_COMPLETED]
    WS-->>Dashboard: Reveal explainable logic chain & confidence
    CallMgr->>Advisor: Fetch localized checklists & helplines
    Advisor->>WS: Broadcast [DOCUMENT_ADVISOR_READY]
    WS-->>Dashboard: Render documents checklist & nearest office
    CallMgr->>Carrier: PlayLocalizedTTSResponse()
    CallMgr->>WS: Broadcast [VOICE_RESPONSE_STARTED]
    Carrier->>Farmer: Synthesized Punjabi/Hindi readback audio
    CallMgr->>WS: Broadcast [CALL_COMPLETED]
    WS-->>Dashboard: Render performance latency statistics
```
