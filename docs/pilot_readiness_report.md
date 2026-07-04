# Kisan Mitra AI — Pilot Readiness Report

This report evaluates Kisan Mitra AI's system components, security posture, performance limits, and operational checklists ahead of the initial MVP pilot launch.

---

## 1. Compliance Audit & Checklist

| Check Category | Validation Script / Test Method | Status | Remarks |
| :--- | :--- | :--- | :--- |
| **Integrations** | `test_integrations_production.py` | **PASSED** | Real HTTP clients verified, fallback to mock is active. |
| **Hardening** | `test_production_readiness.py` | **PASSED** | Defends against common exploits via CSP, HSTS, X-Frame. |
| **Budgets & Caps**| `test_ai_platform.py` | **PASSED** | Daily budget limits enforce hard spending ceilings. |
| **Privacy Compliance**| `test_personalization.py` | **PASSED** | Right to be Forgotten fully deletes profiles and memories on request. |
| **Resilience** | Cascade fallback verification | **PASSED** | Failed APIs gracefully recover or query fallback adapters. |

---

## 2. Performance Verification

### Latency Profiles
* **Reasoning Platform Cached Queries**: `< 10ms` response times.
* **Standard Advisory Queries (Mock Provider)**: `< 50ms` response times.
* **Real Cloud LLM API Calls (Gemini/OpenAI)**: `1.2s - 2.8s` response times (dependent on network speeds and token sizes).

### Resource Consumption (Local container benchmarks)
* **Backend Memory Overhead**: `~120MB` RAM.
* **Frontend Memory Overhead**: `~90MB` RAM.
* **CPU Idle**: `< 1%` CPU utilization.
* **Disk Footprint**: `< 300MB` total container space (inclusive of node/python packages).

---

## 3. Pilot Deployment Target List

1. **Host Server VM**: AWS EC2 t3.medium / Azure Standard_D2s_v3 (2 vCPU, 4GB RAM).
2. **Environment settings**: Production-ready keys for Gemini/OpenAI, Twilio SMS, and Google Speech APIs.
3. **Database Volume Mapping**: Mount Host `./data` to container `/backend/data` to ensure persistent storage of farmer profiles across server restarts.
4. **Log Schedules**: Hourly log rotations via syslog; daily cron jobs triggering `scripts/backup.py` and pushing compressed zip archives to off-site cloud storage.
