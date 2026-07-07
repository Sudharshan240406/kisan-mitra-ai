# Predictive Digital Twin Engine

The **Predictive Digital Twin Engine** upgrades the farmer's static agricultural profile into an active, predictive model. It leverages history, soil logs, and geography to run dynamic forecasts and quantify operational hazards.

---

## 1. Package Structure

The engine code is located under `backend/app/digital_twin/`:

```
backend/app/digital_twin/
├── __init__.py                # Package module exports
├── twin_engine.py              # PredictiveTwin data model and evidence schemas
├── profile_builder.py          # Unified profile input state compiler
├── prediction_engine.py        # Next crop, water demand, and income trend forecasting
├── risk_engine.py              # Weather, crop loss, and financial hazard calculators
├── recommendation_engine.py    # Proactive advisory recommendation alerts
└── twin_manager.py            # Lifecycle coordinator and API routing engine
```

---

## 2. Predictive Models & Risk Algorithms

### Prediction Engine
- **Next Crop**: Suggests the optimal cereal/legume crop rotation based on historical outcomes (e.g. Wheat $\leftrightarrow$ Rice cycle).
- **Water Demand**:
  $$\text{Water Demand (Liters)} = \text{Land Size (Acres)} \times 500,000 \times \text{Crop Coeff} \times \text{Irrigation Coeff}$$
  - *Crop Coefficients*: Rice: `1.5`, Cereals: `1.0`.
  - *Irrigation Coefficients*: Drip/Sprinkler: `0.6` (40% saving), Canal: `0.9`, Rainfed: `1.15`.
- **Disease Probability**: Geographically scaled probability of pathogen infection matching region and crop suitability traits.
- **Income Trend**: Projections calculated from budget capacity spent vs outcome success ratios.

### Risk Engine
- **Weather Risk**: Driven by agro-climatic zone classifications (`arid` = 0.70, `semi-arid` = 0.50, `humid` = 0.30).
- **Crop Failure Risk**: Factoring water supply vulnerability:
  $$\text{Crop Failure Risk} = (\text{Weather Risk} \times 0.8) + \text{Vulnerability Offset}$$
  - *Offsets*: Rainfed: `+0.25`, Drip/Sprinkler: `-0.15`.
- **Composite Recommendation Risk**: Combined risk weighting operational factors:
  $$\text{Rec Risk} = 0.25 \times \text{Weather} + 0.30 \times \text{Failure} + 0.25 \times \text{Disease} + 0.20 \times \text{Financial}$$

---

## 3. Sequence Diagram

The following diagram illustrates how the Predictive Digital Twin coordinates during an interaction query:

```mermaid
sequence-name Predictive Digital Twin Request Flow
sequenceDiagram
    autonumber
    actor Farmer
    participant UI
    participant Orchestrator as AgentOrchestrator
    participant TwinMgr as TwinManager
    participant Chief as ChiefReasoningAgent
    participant Memory as MemoryEngine

    Farmer->>UI: Submits Query ("Wheat rust help")
    UI->>Orchestrator: execute_query(Request)
    
    rect rgb(230, 240, 255)
        note right of Orchestrator: Step 1: Load Twin & Run Predictions
        Orchestrator->>TwinMgr: get_twin(farmer_id)
        TwinMgr-->>Orchestrator: Returns PredictiveTwin
        Orchestrator->>TwinMgr: predict(farmer_id)
        Orchestrator->>TwinMgr: calculate_risk(farmer_id)
    end

    rect rgb(240, 248, 240)
        note right of Orchestrator: Step 2: Inject RAG & Twin Evidence
        Orchestrator->>Chief: reason(query, evidence=[RAG, DigitalTwinEvidence])
        Chief-->>Orchestrator: Returns TrustedRecommendation
    end

    rect rgb(255, 245, 230)
        note right of Orchestrator: Step 3: Auto-Update Twin properties
        Orchestrator->>Memory: save_memory(interaction)
        Orchestrator->>TwinMgr: update_twin_from_interaction(query, response)
        note over TwinMgr: Extracts crops / locations<br/>Re-runs prediction models
    end

    Orchestrator-->>UI: Returns StandardResponse
    UI-->>Farmer: Displays Proactive Advice
```

---

## 4. REST API Endpoints

* **GET** `/api/v1/personalization/twin/{farmer_id}/predictive`
  - Returns the full Predictive Digital Twin document.
* **GET** `/api/v1/personalization/twin/{farmer_id}/predict`
  - Runs and returns prediction forecasts.
* **GET** `/api/v1/personalization/twin/{farmer_id}/risk`
  - Runs and returns risk assessments.
* **GET** `/api/v1/personalization/twin/{farmer_id}/recommendations`
  - Returns proactive recommendations based on forecast assessments.
