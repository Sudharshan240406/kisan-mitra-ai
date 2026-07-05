# Kisan Mitra AI — Operations, Maintenance & Troubleshooting Manual

This manual provides instructions for system operations, regular database/cache maintenance, and troubleshooting typical runtime errors for Kisan Mitra AI.

---

## 1. Operations Manual

### 1.1 Service Controls

#### Start All Services (Docker)
```bash
docker-compose up --build -d
```

#### Stop All Services
```bash
docker-compose down
```

#### Check Active Logs
```bash
# Stream backend application logs
docker-compose logs -f backend
```

---

### 1.2 System Health Monitoring

Administrators should monitor system health via the built-in JSON liveness endpoint:
- **API URL**: `http://localhost:8000/api/v1/health/health`
- **Verification Alert Trigger**: Alert when `"status"` is not `"healthy"` or components report `"disconnected"`.

---

## 2. Maintenance Manual

### 2.1 Database Backups (PostgreSQL)

To perform a hot-backup of the PostgreSQL database without downtime:

```bash
# Execute pg_dump inside the running db container
docker-compose exec db pg_dump -U postgres kisan_mitra_db > kisan_mitra_backup_$(date +%F).sql
```

To restore the backup:
```bash
docker-compose exec -T db psql -U postgres kisan_mitra_db < kisan_mitra_backup.sql
```

---

### 2.2 Redis Cache Management

If Active Sessions or Mandi prices caches become corrupted, clear the cache safely:

```bash
# Flush Redis DB keys
docker-compose exec cache redis-cli flushall
```

---

## 3. Troubleshooting Guide

Below are typical runtime errors, diagnostics, and recovery actions:

### Symptom 1: WebSocket Connection Closes (Offline state on Dashboard)
- **Log Diagnostic**: `WebSocket disconnect...` or `Too many connections` in `backend/logs/app.log`.
- **Reason**:
  - The client limit `MAX_CONNECTIONS = 50` has been reached, or Nginx timed out the socket.
- **Recovery Action**:
  - Increase connection limit in `websocket.py` if needed.
  - Verify Nginx configuration has `proxy_read_timeout 86400s;` and `proxy_http_version 1.1;` set.

### Symptom 2: Database Connection Timeout
- **Log Diagnostic**: `sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection timeout`
- **Reason**:
  - PostgreSQL container is boot-looping or firewalled.
- **Recovery Action**:
  - Check container state via `docker-compose ps`.
  - Inspect Postgres logs: `docker-compose logs db`.

### Symptom 3: Scheme Recommendation Returns Default Fallbacks
- **Log Diagnostic**: `[SpecializedAgent] API error from LLM Provider...`
- **Reason**:
  - Invalid, expired, or rate-limited Gemini/OpenAI API keys.
- **Recovery Action**:
  - Verify `GEMINI_API_KEY` is loaded and active. Run `python -c "import os; print(os.environ.get('GEMINI_API_KEY'))"` on the host machine.
