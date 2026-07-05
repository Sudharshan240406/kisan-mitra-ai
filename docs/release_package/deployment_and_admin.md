# Kisan Mitra AI — Deployment Architecture & Administrator Guide

This document outlines the container deployment model, configuration variables, system startup guides, and server health check instructions for system administrators.

---

## 1. Container Deployment Diagram

The following diagram maps the network partitions, container boundaries, port mappings, and persistent volume definitions:

```mermaid
graph TD
    classDef container fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef volume fill:#0f172a,stroke:#a855f7,stroke-width:2px,color:#f8fafc;
    classDef network fill:#0f172a,stroke:#10b981,stroke-width:2px,color:#f8fafc;

    subgraph HostSystem["Docker Host Machine"]
        subgraph PublicAccess["Public Port Mappings"]
            Port80["Port 80 (HTTP)"]
            Port3000["Port 3000 (React)"]
            Port8000["Port 8000 (FastAPI)"]
        end

        subgraph ContainerStack["Multi-Container Application Services"]
            Proxy["Proxy Server Container (Nginx)"]:::container
            Frontend["Frontend App Container (Next.js)"]:::container
            Backend["Backend ASGI Container (Uvicorn/FastAPI)"]:::container
            Cache["In-Memory Cache Container (Redis)"]:::container
            DB["Relational Database Container (PostgreSQL)"]:::container
            VectorDB["Vector Database Container (ChromaDB)"]:::container
        end

        subgraph PersistentStorage["Docker Persistent Volumes"]
            PGData["postgres_data Volume"]:::volume
            RedisData["redis_data Volume"]:::volume
            ChromaData["chroma_data Volume"]:::volume
            LogsData["backend_logs Volume"]:::volume
        end
        
        BridgeNetwork["kisan_network (Docker Bridge)"]:::network
    end

    %% Network Connections
    Proxy <-->|Routes on Bridge| BridgeNetwork
    Frontend <-->|Routes on Bridge| BridgeNetwork
    Backend <-->|Routes on Bridge| BridgeNetwork
    Cache <-->|Routes on Bridge| BridgeNetwork
    DB <-->|Routes on Bridge| BridgeNetwork
    VectorDB <-->|Routes on Bridge| BridgeNetwork

    %% Port Bindings
    Port80 ===> Proxy
    Port3000 ===> Frontend
    Port8000 ===> Backend

    %% Volume Mounts
    DB --->|Mounts to /var/lib/postgresql/data| PGData
    Cache --->|Mounts to /data| RedisData
    VectorDB --->|Mounts to /chroma/data| ChromaData
    Backend --->|Mounts to /backend/logs| LogsData
```

---

## 2. Administrator Guide

### 2.1 Server Requirements & Sizing

| Metric | Minimum Specification | Recommended Specification |
|--------|-----------------------|---------------------------|
| **VCPU** | 2 Cores | 4 Cores |
| **System Memory** | 4 GB | 8 GB |
| **Storage Space** | 20 GB (SSD) | 50 GB (SSD) |
| **OS Environment** | Ubuntu 22.04 LTS | Rocky Linux 9 / Debian 12 |

---

### 2.2 Pre-Flight Installation Checklist

1. **Docker Engine**: Install Docker version 24.0 or higher.
2. **Docker Compose**: Ensure `docker-compose-plugin` (version 2.20+) is available.
3. **Environment Setup**: Copy `.env.example` to `.env` and fill in:
   - `GEMINI_API_KEY` (Required for LLM specialized agents fallback).
   - `DB_PASSWORD` (Replace default passwords).
4. **Hosts Config**: Verify local DNS / Nginx proxy redirects requests to Port 80.

---

### 2.3 One-Click Startup Procedures

#### On Windows (Development / Local Demo)
We have packaged a simple PowerShell launcher at the repository root:

```powershell
.\start.ps1
```

This starts:
- Uvicorn backend server on `http://localhost:8000` in a dedicated command shell.
- Next.js development server on `http://localhost:3000` in a second command shell.

#### On Linux (Production Containerized)
Execute standard Docker compose boot sequence:

```bash
# Build and run containers in detached mode
docker-compose up --build -d

# Verify container statuses and healthchecks
docker-compose ps
```

---

### 2.4 Maintenance & Diagnostic Logs

To inspect logs from the container stack:

```bash
# View backend application logs
docker-compose logs -f backend

# View reverse proxy Nginx routing logs
docker-compose logs -f proxy

# In case of DB errors, check postgres startup logs
docker-compose logs -f db
```
