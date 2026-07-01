# Operations & Troubleshooting Manual

This manual provides day-to-day operations procedures, log inspection paths, and diagnostic strategies for the **Kisan Mitra AI** platform.

---

## Log Auditing

Backend logs are centralized inside the persistent volume and mapped locally.

### Log File Paths
*   **`logs/app.log`**: Contains all application messages (INFO level and above).
*   **`logs/error.log`**: Dedicated log stream for warnings, errors, and severe crash dump stacks.
*   **`logs/security.log`**: Logs authorization checks, policy interventions, and validation violations.
*   **`logs/audit.log`**: Tracks governance actions, prompting overrides, and database migration traces.

### Inspecting Docker Container Logs
To follow live output logs from active containers:
```bash
# Follow FastAPI backend logs
docker compose logs -f backend

# Follow Nginx proxy routing logs
docker compose logs -f proxy
```

---

## Diagnostic Endpoint Metrics

Examine the aggregated system metrics via the HTTP GET API:
```bash
curl -s http://localhost/api/v1/telemetry/metrics | jq
```
This payload aggregates:
*   Planning, reasoning, and verifier agent latencies.
*   API request error rates.
*   Container system usage (CPU and Memory bytes).

---

## Common Issues & Troubleshooting Runbook

### 1. Nginx returns 502 Bad Gateway
*   **Cause**: The backend FastAPI container is offline or restarting.
*   **Action**:
    Check backend status: `docker compose ps backend`.
    Inspect backend log traces for configuration check violations: `docker compose logs backend`.

### 2. Startup fails with `PRODUCTION SECURITY VIOLATION`
*   **Cause**: The application is running in production mode (`APP_ENV=production`) but has default database credentials or missing LLM API keys.
*   **Action**: Check and edit the root `.env` profile to ensure all credentials differ from defaults.

### 3. API Limit Exceeded (Nginx 429 Too Many Requests)
*   **Cause**: Rate-limiting triggered (limits set to 10 requests/sec per client IP with a burst rate of 20).
*   **Action**: If limits are too restrictive for staging/internal benchmarks, adjust `limit_req_zone` settings inside `deployment/nginx/nginx.conf` and reload Nginx:
    ```bash
    docker compose exec proxy nginx -s reload
    ```
