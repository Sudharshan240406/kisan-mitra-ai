# Production Readiness Checklist

Use this pre-flight checklist to verify security, performance, and stability configs before launching **Kisan Mitra AI** into production.

---

## 1. Credentials & Secrets
* [ ] **DB Password**: Changed from `postgres` and set to a long, randomized string.
* [ ] **DB User**: Custom user name configured (not `postgres`).
* [ ] **LLM API Keys**: Valid keys for active providers (`GEMINI_API_KEY`, `OPENAI_API_KEY`) set.
* [ ] **No Hardcoded Values**: Verified that no secrets are committed in source files.

---

## 2. Environment Settings
* [ ] **APP_ENV**: Configured to `production`.
* [ ] **DEBUG**: Set to `false`.
* [ ] **LOG_LEVEL**: Set to `info` or `warn` (avoid `debug`).
* [ ] **LOG_FORMAT**: Set to `json` for structured logging compatibility.

---

## 3. Network & Routing Security
* [ ] **CORS Origins**: Standard dev wildcards (`*`) removed; domains limited to target frontend hosts.
* [ ] **Nginx Reverse Proxy**: Listening on port 80/443, routing traffic through internal Docker network.
* [ ] **Security Headers**: HSTS, Content-Security-Policy (CSP), and X-Frame-Options configured.
* [ ] **Request Size Cap**: `client_max_body_size` capped at 10M.
* [ ] **Rate Limiting**: Rate limits enabled in Nginx config.

---

## 4. Container Optimization
* [ ] **Multi-stage Builds**: Used in both `backend.Dockerfile` and `frontend.Dockerfile` for small footprint.
* [ ] **Non-root Context**: Processes run as custom `appuser` and `node` system users.
* [ ] **Health Checks**: Containers have active liveness/readiness health probes.

---

## 5. Operations & Logs
* [ ] **Log Rotation**: Active `RotatingFileHandler` with caps set.
* [ ] **Persistent Volumes**: Named volumes allocated for database data, redis cache, chroma, and log directories.
* [ ] **Backup Tests**: Backup script (`backup.py`) and restore script (`restore.py`) verified.
* [ ] **CI/CD quality gates**: Quality check gates (ruff, black, mypy, pytest) passing on branches.
