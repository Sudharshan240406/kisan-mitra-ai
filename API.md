# API Documentation & Contracts

This document records the REST endpoints, simulation triggers, and WebSocket payload interfaces exposed by Kisan Mitra AI.

---

## 1. REST Endpoints

### A. Demo Farmers Registry
* **`GET /api/v1/demo/farmers`**
  * Description: Lists all registered demo farmer profiles (Ramesh Patel, Lakshmi, etc.).
  * Response: Array of Farmer profiles.

### B. Welfare Schemes Eligibility Engine
* **`GET /api/v1/demo/schemes/{farmer_id}`**
  * Description: Evaluates a farmer profile against the 11 agricultural welfare yojana policies.
  * Response:
    ```json
    {
      "farmer_id": "...",
      "farmer_name": "...",
      "total_schemes_evaluated": 11,
      "eligible_count": 4,
      "possibly_eligible_count": 2,
      "recommendations": [
        {
          "scheme_id": "pm-kisan",
          "title": "...",
          "status": "ELIGIBLE",
          "confidence": 0.98,
          "reasoning": ["..."],
          "evidence": ["..."],
          "benefits": "...",
          "required_documents": ["..."],
          "missing_documents": []
        }
      ]
    }
    ```

### C. Ingress Simulators
* **`POST /api/v1/demo/simulate-call/{farmer_id}`**
  * Description: Triggers a simulated IVR call pipeline for a demographic farmer, broadcasting events on the WebSocket channel.

---

## 2. WebSocket Gateway

* **URL**: `ws://localhost:8000/ws/live`
* **Protocol**: JSON payloads
* **Event Sequence**:
  * `CALL_STARTED`
  * `CALLER_IDENTIFIED`
  * `DIGITAL_TWIN_LOADED`
  * `SCHEME_SEARCH_STARTED`
  * `SCHEME_MATCHED`
  * `ELIGIBILITY_COMPLETED`
  * `REASONING_COMPLETED`
  * `DOCUMENT_ADVISOR_READY`
  * `VOICE_RESPONSE_STARTED`
  * `CALL_COMPLETED`
  * `CALL_ERROR`
