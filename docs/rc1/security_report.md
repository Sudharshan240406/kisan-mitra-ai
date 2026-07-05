# Kisan Mitra AI — Release Candidate 1 (RC1) Security Report

This document outlines the security controls, validation rules, privacy protections, and dependency reviews conducted for the Release Candidate 1 (RC1).

---

## 1. Credentials Isolation

- **Secret Key Segregation**: All core keys (Gemini, OpenAI, LangChain) are completely isolated in environment variables. No secrets are hardcoded in the codebase.
- **Example Template**: `.env.example` lists all necessary parameters (like `DEMO_MODE` and `WS_MAX_CONNECTIONS`) with dummy credentials.
- **Production Mode Validation**: The lifespan loader executes `validate_production_config(settings)` at startup. If `APP_ENV=production` is set, it checks that standard sandbox variables are replaced with production-grade keys.

---

## 2. API & Network Hardening

- **CORS Restrictive Settings**: Configured origins are limited to registered domains. Wildcards are disabled.
- **Content Security Policy (CSP)**: Handled via FastAPI HTTP middleware. Added `connect-src` parameters supporting both `ws://` and `wss://` WebSocket protocols to prevent cross-site scripting blocking.
- **Rate-Limiting Guard**: Capped concurrent WebSocket streams to `50` to safeguard against connection pool exhaustion.
- **Input Sanitization**: Request bodies are validated using Pydantic schemas, blocking malformed structural payloads.
- **Injection Mitigation**: Database integrations run via SQLAlchemy ORM, eliminating SQL injection vulnerabilities.

---

## 3. Privacy & Compliance

- **PII Scrubbing**: Logging configurations prevent plain-text phone numbers and names from being written to the logs. Callers are referenced using UUID session logs.
- **Database Column Encryption**: Storage mapping reserves column-level AES encryption fields for Aadhaar or bank passbook parameters.
