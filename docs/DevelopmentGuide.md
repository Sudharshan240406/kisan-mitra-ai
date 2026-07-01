# Kisan Mitra AI - Development Guide

This document provides a comprehensive guide for developers setting up the local development environment for the **Kisan Mitra AI** project.

---

## 1. Prerequisites

Ensure you have the following software installed locally:
- **Python**: 3.12 or newer.
- **Node.js**: 20.x or newer (includes `npm`).
- **Docker**: Desktop version supporting `compose`.
- **Git**: For version control.

---

## 2. Backend Setup (Local)

1.  **Navigate into the backend directory**:
    ```bash
    cd backend
    ```
2.  **Create a Virtual Environment**:
    ```bash
    python -m venv .venv
    ```
3.  **Activate the Virtual Environment**:
    *   **Windows (PowerShell)**:
        ```powershell
        .\.venv\Scripts\Activate.ps1
        ```
    *   **macOS / Linux**:
        ```bash
        source .venv/bin/activate
        ```
4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
5.  **Environment Variables**:
    Copy the root `.env.example` to `backend/.env` (which is git-ignored) and fill in the necessary keys.
6.  **Run Development Server**:
    ```bash
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    ```
7.  **Verify Running Server**:
    - Root Endpoint: [http://localhost:8000/](http://localhost:8000/)
    - Health Endpoint: [http://localhost:8000/health](http://localhost:8000/health)
    - Swagger Docs UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 3. Frontend Setup (Local)

1.  **Navigate into the frontend directory**:
    ```bash
    cd frontend
    ```
2.  **Install dependencies**:
    ```bash
    npm install
    ```
3.  **Run Next.js Dev Server**:
    ```bash
    npm run dev
    ```
4.  **Verify running application**:
    Open [http://localhost:3000/](http://localhost:3000/) in your browser. It should render a dark layout with the heading **Kisan Mitra AI**.

---

## 4. Docker Compose Setup (Recommended)

To run the complete workspace locally with its databases, memory caches, vector registers, and web servers:

1.  **Copy Environment Variables**:
    Create `.env` file from the example in the root:
    ```bash
    cp .env.example .env
    ```
2.  **Spin up Services**:
    ```bash
    docker compose up --build
    ```
3.  **Spin down Services**:
    ```bash
    docker compose down
    ```
4.  **Remove Persistent Volumes (e.g. databases, cache contents)**:
    ```bash
    docker compose down -v
    ```
