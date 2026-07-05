# Kisan Mitra AI — Production Deployment Guide

This guide details instructions for launching Kisan Mitra AI in production, including Docker compose, environment setups, and proxy mappings.

---

## 1. Docker Compose Stack Architecture

We use multi-container orchestration. The service topology is defined in `docker-compose.yml`:

```
                    ┌─────────────────────────┐
                    │      Nginx Proxy        │ (Port 80)
                    └────────────┬────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
     ┌───────────────────────┐       ┌───────────────────────┐
     │   FastAPI Backend     │       │   Next.js Frontend    │ (Port 3000)
     └───────────┬───────────┘       └───────────────────────┘
                 │
   ┌─────────────┼─────────────┐
   ▼             ▼             ▼
┌─────┐      ┌───────┐     ┌───────────┐
│ DB  │      │ Cache │     │ Vector DB │
└─────┘      └───────┘     └───────────┘
```

- **`db`** (PostgreSQL 16): Persistent transaction and profile store.
- **`cache`** (Redis 7): In-memory session state, DTMF cache, and rate limit tracking.
- **`vector_db`** (ChromaDB): Vector storage for semantic scheme lookups.
- **`backend`** (Uvicorn): ASGI application layer running FastAPI.
- **`frontend`** (Next.js): Server-side rendered interface.
- **`proxy`** (Nginx): Reverse proxy handling SSL termination and static asset caching.

---

## 2. Environment Configurations

Copy `.env.example` to `.env` and fill in active keys:

```bash
# Environment
APP_ENV=production
DEBUG=false

# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_postgres_pass
POSTGRES_DB=kisan_mitra_db
DATABASE_URL=postgresql://postgres:secure_postgres_pass@db:5432/kisan_mitra_db

# Cache Configuration
REDIS_HOST=cache
REDIS_PORT=6379

# LLM Providers (Required for production agents)
GEMINI_API_KEY=AIzaSy...
OPENAI_API_KEY=sk-...

# Demo Settings
DEMO_MODE=true
WS_MAX_CONNECTIONS=50
```

---

## 3. Backend Deployment (FastAPI)

For manual/non-containerized hosting on a Linux instance:

### Service Configuration (systemd)
Create `/etc/systemd/system/kisan-backend.service`:

```ini
[Unit]
Description=Kisan Mitra Backend Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/var/www/kisan-mitra-ai/backend
EnvironmentFile=/var/www/kisan-mitra-ai/backend/.env
ExecStart=/home/ubuntu/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --log-config logging.conf
Restart=always

[Install]
WantedBy=multi-user.target
```

### Health Check Endpoint
- URL: `http://localhost:8000/api/v1/health/health`
- Method: `GET`
- Response Payload:
  ```json
  {
    "status": "healthy",
    "service": "KisanMitraAI",
    "components": {
      "database": "connected",
      "cache": "connected",
      "vector_db": "connected"
    }
  }
  ```

---

## 4. Frontend Deployment (Next.js)

### Production Build compilation
Always run the Next.js compiler with the Turbopack engine disabled for maximum production stability:

```bash
cd frontend
npm install
npm run build
```

This generates optimized static page templates in the `.next/` directory.

---

## 5. Reverse Proxy Mappings (Nginx)

The reverse proxy routes HTTP and WebSocket streams seamlessly:

```nginx
server {
    listen 80;
    server_name kisanmitra.in;

    # Static next.js assets
    location /_next/static/ {
        alias /var/www/kisan-mitra-ai/frontend/.next/static/;
        expires 365d;
        access_log off;
    }

    # Live Event Stream WebSocket router
    location /ws/live {
        proxy_pass http://localhost:8000/ws/live;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400s;
    }

    # REST APIs
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Frontend pages
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
    }
}
```
