# Kisan Mitra AI — Production Security Checklist

This document details the security practices and compliance guidelines required for deploying Kisan Mitra AI into production environments.

---

## 1. Credentials & Secrets Management

- **No Hardcoded Keys**: Verify that no API credentials (Gemini, OpenAI, LangChain) or database passwords are hardcoded inside any Python module or configuration file.
- **Environment Separation**: Always leverage environment variables (`.env` or Docker env configurations). `.env` files must be added to `.gitignore`.
- **Secret Rotation Schedule**: Production API keys and database credentials should be rotated every 90 days.
- **Vault Integration**: In production (AWS/Azure/GCP), transition from `.env` files to cloud secret stores:
  - AWS Secrets Manager / GCP Secret Manager / HashiCorp Vault.

---

## 2. API Security & Rate Limiting

- **WebSocket Limits**: Enforcement of the `MAX_CONNECTIONS = 50` threshold inside `ConnectionManager` to prevent denial-of-service (DoS) attacks.
- **REST Rate Limiting**: Enable rate limiting on all public API endpoints using `slowapi` or redis-backed limiters.
- **Cross-Origin Resource Sharing (CORS)**: Set `CORS_ORIGINS` to the exact production frontend domains (do not use `*` wildcard).
- **Input Sanitization**:
  - Pydantic models automatically validate incoming request JSON structures.
  - SQL Injection Defense: Ensure all database interactions utilize the SQLAlchemy ORM query engine, avoiding raw text queries.

---

## 3. PII & Logger Compliance

To remain compliant with local regulations (such as Digital Personal Data Protection Act, DPDP), logging must be clean of PII:

- **Phone Numbers**: Log files must mask phone numbers.
  - *Correct*: `Call started for caller +91******3210`
  - *Incorrect*: `Call started for caller +919876543210`
- **Farmer Names**: Scrub names from trace metrics logs. Keep logs focused on system events and UUIDs.
- **Database Encrypted Columns**: Store sensitive farmer fields (e.g., Aadhaar number or Bank details) using column-level encryption (AES-256) inside PostgreSQL.

---

## 4. Final Deploy Checklist

| # | Security Guard | Status | Verification Command |
|---|----------------|--------|----------------------|
| 1 | Is Debug Mode disabled? | [ ] | Check `DEBUG=false` in `.env` |
| 2 | Are production database defaults changed? | [ ] | Check `DB_PASSWORD` does not equal `postgres` |
| 3 | Is CORS restricted? | [ ] | Check `settings.CORS_ORIGINS` in `main.py` |
| 4 | Are HTTP security headers set? | [ ] | Verify CSP connect-src and X-Frame-Options |
| 5 | Are logs free of unmasked PII? | [ ] | Inspect `/var/log/app.log` |
| 6 | Are API calls rate limited? | [ ] | Verify limit handlers in main entrypoint |
