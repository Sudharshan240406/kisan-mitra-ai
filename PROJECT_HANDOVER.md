# Kisan Mitra AI — Project Handover Guide

**System:** Kisan Mitra AI — Autonomous Multi-Lingual Agricultural AI  
**Version:** v1.0 — Production Candidate  
**Date:** July 21, 2026  

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python:** Python 3.11+ installed and on PATH
- **Node.js:** Node.js v18+ and npm installed
- **Git:** Installed for repository tracking
- **Ollama (Optional for local LLM inference):** Installed and running locally on port 11434

---

## ⚙️ Environment Setup

1. **Clone Repository:**
   ```bash
   git clone <repo-url>
   cd kisan-mitra-ai
   ```

2. **Backend Setup:**
   ```bash
   # Create virtual environment (optional)
   python -m venv venv
   # Windows PowerShell activation:
   .\venv\Scripts\Activate.ps1

   # Install dependencies
   pip install -r pyproject.toml # or pip install fastapi uvicorn pydantic pytest
   ```

3. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

---

## 🏃 Commands to Run the Application

### Running Backend Server
```bash
# From workspace root:
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend
```
- API Base URL: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`

### Running Frontend Server
```bash
# From workspace root:
npm --prefix frontend run dev
```
- Frontend Web Interface: `http://localhost:3000`

### Running Automated Test Suites
```bash
# Run 367 backend unit & integration tests:
python -m pytest backend/tests

# Run multi-lingual verification script:
python scripts/verify_languages.py

# Run frontend production build check:
npm --prefix frontend run build
```

---

## 🦙 Ollama Local LLM Integration (Optional)

If local offline LLM inference is required:
1. Install Ollama from [ollama.ai](https://ollama.ai).
2. Pull required models:
   ```bash
   ollama pull llama3:8b
   ```
3. Verify Ollama service is running on `http://localhost:11434`.

---

## 📲 How to Run Demo Mode (Judge Presentation)

1. Start both Backend (`port 8000`) and Frontend (`port 3000`).
2. Open browser to `http://localhost:3000`.
3. Click **"Launch Live Phone Call"** in the top navigation or main dashboard.
4. Select any of the 6 realistic farmer archetypes (e.g. *Ramesh Singh - Punjab*, *Lakshmi Devi - Rajasthan*, *Priya Kumari - Karnataka*).
5. Choose from the **10 conversation languages** using the language dropdown.
6. Interact by clicking sample questions or using microphone speech.

---

## 🛠 Troubleshooting

- **Port 8000 in use:**  
  Stop existing Python process or run Uvicorn on a different port: `--port 8001` (update `NEXT_PUBLIC_API_URL` in `.env.local` if modified).
- **Frontend build warning on lockfiles:**  
  Set `turbopack.root` in `frontend/next.config.ts` if running turbopack outside standard root directory.

---

## 📁 Repository Structure Overview

```
kisan-mitra-ai/
├── backend/
│   ├── agents/          # LangGraph & Multi-agent scheme solvers
│   ├── app/
│   │   ├── api/v1/      # FastAPI REST & WebSocket endpoints (demo.py, websocket.py)
│   │   ├── core/        # Container DI, settings, telemetry
│   │   ├── models/      # Farmer & scheme Pydantic models
│   │   └── services/    # DemoService, EligibilityEngine, DocumentAdvisor
│   └── tests/           # 367 pytest verification test cases
├── frontend/
│   ├── app/             # Next.js App Router pages
│   ├── components/      # UI components & smartphone call screen demo
│   └── hooks/           # useDemoCallSession, Speech Recognition & TTS hooks
├── scripts/             # Verification & seeding scripts (verify_languages.py)
├── RELEASE_NOTES.md     # Production Candidate release notes
└── PROJECT_HANDOVER.md  # Handover documentation
```
