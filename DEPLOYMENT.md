# Deployment & Production Launch Guide

This document outlines environment variables configurations, Docker Compose guidelines, and production checklists for deploying Kisan Mitra AI.

---

## 1. Local Development Launch

Ensure you have Python 3.11+ and Node.js 18+ installed on your system.

### A. Launch Backend Service
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000 --reload
```

### B. Launch Next.js Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in the browser.

---

## 2. Docker Compose Deployments

Deploy the entire stack (FastAPI gateway, Next.js frontend, Redis, ChromaDB, and PostgreSQL) via:

```bash
docker-compose up --build -d
```

---

## 3. Production Environment Checklist

Ensure the following variables are defined in the production `.env` config file:

| Variable Name | Description | Recommended Production Value |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection link | Secure DB endpoint |
| `REDIS_URL` | Redis connection URL | Secure cache cluster link |
| `GEMINI_API_KEY` | Google Gemini key | Production API Key |
| `NEXT_PUBLIC_API_URL` | Frontend API target | `https://api.yourdomain.com` |
| `NEXT_PUBLIC_WS_URL` | Frontend WebSocket target | `wss://api.yourdomain.com/ws/live` |
