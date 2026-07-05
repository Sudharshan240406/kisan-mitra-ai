# Kisan Mitra AI — Release Notes (v1.0-RC1)

This document contains the official release notes, system limitations, future roadmap, and pre-flight deployment checklist for Kisan Mitra AI Release Candidate 1 (RC1).

---

## 1. Version Summary (v1.0-RC1)

Kisan Mitra AI (v1.0-RC1) is a production-quality release candidate designed for enterprise-grade agricultural advisory and government scheme matching. Key features include:

- **E2E Telephony Integration**: A robust 4-step IVR onboarding workflow (Greeting, Language Selection, Caller Identification, Intent Capture).
- **Explainable Eligibility Engine**: Dynamic rule-based matching against 11 core schemes with step-by-step reasoning chains.
- **Mission Control Operations Dashboard**: Real-time WebSocket streaming of 13 lifecycle events, digital twin snapshots, and progressive scheme matching.
- **Security Hardening**: Enforced security headers, restricted CORS, WebSocket rate limits (`MAX_CONNECTIONS=50`), and PII logs masking.

---

## 2. Known Limitations

1. **Simulated State Database Integrations**: Landholding checks evaluate land size from the Digital Twin model instead of executing live state Bhulekh queries.
2. **Mock TTS Synthesis**: The voice response summaries are generated as text and played via mock TTS. Direct speech synthesis (e.g. Google Cloud TTS / Bhashini) must be plugged into the media gateway.
3. **Mandi Market Rates**: Relies on cached historical mandi records. Real-time endpoints require active government Agmarknet developer credentials.

---

## 3. Future Roadmap

1. **Indic LLM Finetuning**: Replace standard models with custom-trained Indic LLMs (e.g., Krutrim / Airavata) optimized for local farming dialects.
2. **Omnichannel Messaging**: Expand support to WhatsApp Business API and Telegram channels, offering structured document guidance via chats.
3. **Live Aadhaar e-KYC Integration**: Integrate with official UIDAI sandbox APIs for biometric and mobile OTP verification.

---

## 4. Pre-Flight Deployment Checklist

- [ ] Confirm all environment keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`) are populated in the `.env` production file.
- [ ] Verify `DEBUG=false` and `APP_ENV=production` are set.
- [ ] Restrict `CORS_ORIGINS` to the exact production frontend domains.
- [ ] Ensure uvicorn is configured with a minimum of 4 worker threads.
- [ ] Check Nginx reverse proxy buffers for infinite WebSocket connections timeouts.
