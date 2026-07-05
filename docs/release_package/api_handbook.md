# Kisan Mitra AI — API Handbook

This document contains a complete technical reference for all REST endpoints, WebSocket live event streams, request/response models, and error statuses of Kisan Mitra AI.

---

## 1. REST Endpoint Specifications

The FastAPI backend exposes **65** total routes. The core operational REST interfaces are outlined below:

### 1.1 Demo & Simulation APIs (`/api/v1/demo`)

#### 1. Retrieve All Demo Farmers
- **Endpoint**: `/api/v1/demo/farmers`
- **Method**: `GET`
- **Headers**: `Accept: application/json`
- **Response Example (200 OK)**:
  ```json
  [
    {
      "farmer_id": "DEMO-F001",
      "name": "Ramesh Singh",
      "phone": "+919876543210",
      "state": "Punjab",
      "district": "Ludhiana",
      "category": "Small",
      "gender": "Male",
      "land_hectares": 2.0,
      "crops": ["Wheat", "Rice"],
      "language": "pa"
    }
  ]
  ```

#### 2. Get Single Farmer Details
- **Endpoint**: `/api/v1/demo/farmers/{farmer_id}`
- **Method**: `GET`
- **Path Parameter**: `farmer_id: str` (e.g. `DEMO-F001`)
- **Response Example (200 OK)**:
  ```json
  {
    "farmer_id": "DEMO-F001",
    "name": "Ramesh Singh",
    "phone": "+919876543210",
    "state": "Punjab",
    "district": "Ludhiana",
    "category": "Small",
    "gender": "Male",
    "land_hectares": 2.0,
    "crops": ["Wheat", "Rice"],
    "language": "pa"
  }
  ```

#### 3. Run Scheme Matching Engine
- **Endpoint**: `/api/v1/demo/schemes/{farmer_id}`
- **Method**: `GET`
- **Path Parameter**: `farmer_id: str`
- **Response Example (200 OK)**:
  ```json
  {
    "farmer_id": "DEMO-F001",
    "farmer_name": "Ramesh Singh",
    "total_schemes_evaluated": 11,
    "eligible_count": 3,
    "recommendations": [
      {
        "scheme_id": "pm-kisan",
        "title": "Pradhan Mantri Kisan Samman Nidhi",
        "status": "ELIGIBLE",
        "confidence": 0.95,
        "benefits": "INR 6,000/year"
      }
    ]
  }
  ```

#### 4. Trigger E2E Call Simulation
- **Endpoint**: `/api/v1/demo/simulate-call/{farmer_id}`
- **Method**: `POST`
- **Path Parameter**: `farmer_id: str`
- **Response Example (200 OK)**:
  ```json
  {
    "success": true,
    "call_id": "DEMO-CALL-DEMO-F001-1683492023",
    "farmer": { "name": "Ramesh Singh", "phone": "+919876543210" },
    "top_scheme": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
    "elapsed_ms": 1120.4,
    "performance_grade": "A"
  }
  ```

---

## 2. WebSocket Event Streams

- **Connection URL**: `ws://localhost:8000/ws/live`
- **Protocol Handshake**: On connect, the socket immediately dispatches:
  ```json
  {
    "type": "CONNECTED",
    "timestamp": 1783228945.12,
    "payload": {
      "message": "Connected to Kisan Mitra Live Event Stream",
      "connected_clients": 1
    }
  }
  ```

### Key Broadcast Events
Below is the payload structure of core pipeline events emitted during call simulations:

#### `CALLER_IDENTIFIED`
```json
{
  "type": "CALLER_IDENTIFIED",
  "timestamp": 1783228945.89,
  "payload": {
    "call_id": "DEMO-CALL-DEMO-F001",
    "farmer_id": "DEMO-F001",
    "farmer_name": "Ramesh Singh",
    "phone": "+919876543210",
    "state": "Punjab",
    "district": "Ludhiana"
  }
}
```

#### `SCHEME_MATCHED`
```json
{
  "type": "SCHEME_MATCHED",
  "timestamp": 1783228946.22,
  "payload": {
    "call_id": "DEMO-CALL-DEMO-F001",
    "scheme_id": "pm-kisan",
    "title": "PM-KISAN",
    "status": "ELIGIBLE",
    "confidence": 0.95,
    "benefits": "INR 6,000/year"
  }
}
```

---

## 3. Global Error Handling Payloads

All endpoints share standard JSON exception envelopes.

### Validation Error (422 Unprocessable Entity)
```json
{
  "detail": [
    {
      "loc": ["body", "digits"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Resource Not Found (404 Not Found)
```json
{
  "detail": "Demo farmer 'DEMO-F099' not found."
}
```
