# Kisan Mitra AI — Release Candidate 1 (RC1) API Inventory

This document details the REST endpoints, schemas, status codes, and security controls verified for the Release Candidate 1 (RC1).

---

## 1. REST API Inventory Summary

Kisan Mitra AI registers **65** total routes inside the FastAPI router engine. Below is a detailed listing of the core runtime APIs:

### 1.1 Demo & Simulation Engine (`/api/v1/demo`)

#### 1. List Demo Farmers
- **Method**: `GET`
- **Path**: `/api/v1/demo/farmers`
- **Request Parameters**: None
- **Response Schema**: `list[dict]` containing farmer summaries
- **HTTP Status Codes**: `200 OK`
- **Authentication**: None (Developer sandbox)

#### 2. Get Farmer Details
- **Method**: `GET`
- **Path**: `/api/v1/demo/farmers/{farmer_id}`
- **Request Parameters**: `farmer_id: str` (path parameter)
- **Response Schema**: `dict` containing farmer profile
- **HTTP Status Codes**: `200 OK`, `404 Not Found` (when farmer does not exist)

#### 3. Run Scheme Eligibility Engine
- **Method**: `GET`
- **Path**: `/api/v1/demo/schemes/{farmer_id}`
- **Request Parameters**: `farmer_id: str` (path parameter)
- **Response Schema**: Complete eligibility verdicts for all 11 schemes
- **HTTP Status Codes**: `200 OK`, `404 Not Found`

#### 4. Trigger Call Simulation Pipeline
- **Method**: `POST`
- **Path**: `/api/v1/demo/simulate-call/{farmer_id}`
- **Request Parameters**: `farmer_id: str` (path parameter)
- **Response Schema**: E2E pipeline execution statistics and transcript
- **HTTP Status Codes**: `200 OK`, `404 Not Found` (Graceful try/except fallback on internal errors)

#### 5. Trigger Multi-Farmer Demo
- **Method**: `POST`
- **Path**: `/api/v1/demo/start`
- **Response Schema**: Cycles sequentially through all 6 farmers
- **HTTP Status Codes**: `200 OK`

---

### 1.2 Telephony Integration APIs (`/api/v1/telephony`)

#### 1. Incoming Call Event
- **Method**: `POST`
- **Path**: `/api/v1/telephony/incoming`
- **Request Body**: `from: str`, `to: str`, `session_id: str`
- **Response Schema**: Initial XML TwiML greeting response
- **HTTP Status Codes**: `200 OK`

#### 2. Caller DTMF Input
- **Method**: `POST`
- **Path**: `/api/v1/telephony/dtmf`
- **Request Body**: `digits: str`, `session_id: str`
- **Response Schema**: Transition instructions
- **HTTP Status Codes**: `200 OK`

---

### 1.3 System Health Checks

#### 1. System Liveness Check
- **Method**: `GET`
- **Path**: `/api/v1/health/health`
- **Response Schema**: Reports liveness of PostgreSQL, Redis, and ChromaDB
- **HTTP Status Codes**: `200 OK`
