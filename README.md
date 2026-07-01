# Kisan Mitra AI

Kisan Mitra AI is an enterprise-grade multi-agent agricultural platform designed to empower farmers with real-time, actionable insights. By orchestrating specialized agents (market, weather, disease diagnosis, schemes, soil, and irrigation), the system provides seamless agronomic advisory through chat, voice (STT/TTS/IVR), and SMS interfaces.

---

## Technical Stack

*   **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui
*   **Backend**: FastAPI, Python 3.12+
*   **AI Orchestration**: LangGraph, LangChain
*   **Database**: PostgreSQL
*   **Vector Search**: ChromaDB (RAG capability)
*   **Cache & Queue**: Redis
*   **Deployment**: Docker & Docker Compose, Render (backend), Vercel (frontend)

---

## Directory Structure

Below is an overview of the key directories in the repository:

```
* backend/
  * app/                   # FastAPI backend implementation
    * api/                 # API routers and endpoints
    * config/              # Configuration schemas
    * core/                # Core modules (logging, configuration, security)
    * database/            # Database connections and migrations
    * dependencies/        # Common dependency injection providers
    * middleware/          # FastAPI middleware (CORS, authentication, logging)
    * models/              # Database models (SQLAlchemy / SQLModel)
    * orchestrator/        # LangGraph agent orchestrators
    * prompts/             # System and agent prompts
    * schemas/             # Pydantic schemas for request/response serialization
    * services/            # Core business logic services
    * utils/               # Helper utilities
    * main.py              # Application entry point
  * agents/                # AI Agent packages
    * base/                # Base agent classes
    * planner/             # Routing and planning agent
    * market/              # Commodity market intelligence agent
    * weather/             # Weather forecast and advisory agent
    * disease/             # Crop disease diagnosis agent
    * schemes/             # Government scheme advisory agent
    * finance/             # Agricultural loan/finance agent
    * irrigation/          # Smart irrigation/water management agent
    * soil/                # Soil health and fertilizer agent
    * translation/         # Multilingual translation agent
    * memory/              # Chat history and context persistence agent
    * verifier/            # Accuracy verifier agent
  * tests/                 # Unit and integration test suites
* frontend/                # Next.js web application
  * app/                   # Next.js pages and layouts (App Router)
  * components/            # Reusable UI component library (shadcn/ui)
  * hooks/                 # React custom hooks
  * lib/                   # Shared libraries (API clients, formatting)
  * public/                # Static assets (images, fonts, icons)
  * services/              # API consumption layer
  * styles/                # Global CSS styles (Tailwind configuration)
* knowledge/               # Static agricultural knowledge base / reference data
  * crops/                 # Crop cultivation guides
  * diseases/             # Disease catalogs and symptoms lists
  * fertilizers/          # Fertilizer schedules and types
  * pesticides/           # Pesticide reference indexes
  * government_schemes/    # Government agricultural program indexes
  * market/                # Historical crop price indices
  * weather/               # Historical weather pattern matrices
  * rag/                   # Embeddings and indexing scripts
* voice/                   # Voice integration module (telephony, interactive voice response)
  * stt/                   # Speech-To-Text processing
  * tts/                   # Text-To-Speech rendering
  * ivr/                   # Interactive Voice Response flows
  * recordings/            # Audio assets and recordings cache
* sms/                     # SMS notification system
  * providers/             # SMS API gateways (e.g., Twilio, Plivo)
  * templates/             # Localization templates for SMS
  * logs/                  # Outgoing SMS logs
* data/                    # Local storage and state databases
  * farmers/               # Farmer profile data cache
  * conversations/         # Local agent conversation logs
  * market_cache/          # Cached market commodity rates
  * weather_cache/         # Cached weather parameters
  * vector_db/             # Local Chroma DB persistence directory
* docs/                    # Technical documentation
  * architecture/          # Multi-agent architecture documents
  * api/                   # API reference docs
  * diagrams/              # Sequence and architecture diagrams
  * roadmap/               # Implementation phases roadmap
  * competition/           # Domain analyses and comparisons
* deployment/              # Configuration files for orchestration and deployment
  * docker/                # Dockerfiles for backend and frontend
  * render/                # Render deployment configuration
  * vercel/                # Vercel frontend configurations
  * nginx/                 # Reverse proxy configuration
* scripts/                 # Utility scripts for database seeding, setup, etc.
```

---

## Setup Instructions

### Prerequisites
*   Python 3.12+
*   Node.js 20+ (with npm)
*   Docker & Docker Compose

### 1. Environment Configuration
Create a `.env` file from the example:
```bash
cp .env.example .env
```
Fill in the appropriate configuration keys in `.env`.

---

## Local Development Instructions

### Running the Backend (FastAPI)

1.  Navigate to the `backend/` directory:
    ```bash
    cd backend
    ```
2.  Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # macOS/Linux:
    source .venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the application using Uvicorn:
    ```bash
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    ```
5.  Access documentation endpoints:
    *   API Root: [http://localhost:8000/](http://localhost:8000/)
    *   Health Check: [http://localhost:8000/health](http://localhost:8000/health)
    *   Swagger UI Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
    *   ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Running the Frontend (Next.js)

1.  Navigate to the `frontend/` directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Run the development server:
    ```bash
    npm run dev
    ```
4.  Access the web application at [http://localhost:3000/](http://localhost:3000/).

---

## Docker Orchestration

To run the complete platform locally using Docker Compose (PostgreSQL, Redis, ChromaDB, FastAPI Backend, Next.js Frontend):

1.  Start the multi-container application:
    ```bash
    docker compose up --build
    ```
2.  Run containers in detached mode:
    ```bash
    docker compose up -d
    ```
3.  Stop all running services:
    ```bash
    docker compose down
    ```
4.  Verify running containers:
    ```bash
    docker compose ps
    ```
