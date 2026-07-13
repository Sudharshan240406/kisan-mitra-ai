# Exotel IVR Demo Integration — Sprint 29

> **Kisan Mitra AI** — End-to-end phone call demo via Exotel.

---

## What This Does

Connects the existing IVR Platform to real phone calls using **Exotel** as the
telephony carrier. A farmer dials the Exotel virtual number → Kisan Mitra
answers → speaks the greeting → processes DTMF/voice → delivers AI advice →
sends an SMS summary after the call.

All business logic (IVR flow, STT, TTS, AI Orchestrator, SMS, Memory) is
unchanged. This sprint only adds the **Exotel wire layer**.

---

## New Files

```
backend/app/ivr/telephony/
├── __init__.py          Package exports
├── exotel_client.py     Exotel REST client + ExoML builders
├── call_bridge.py       Converts CallManager results → ExoML XML
└── webhook.py           FastAPI router — Exotel webhook endpoints
```

---

## Webhook Endpoints

| Method | Path | Triggered by |
|--------|------|--------------|
| `POST` | `/api/v1/exotel/inbound` | Farmer dials in |
| `POST` | `/api/v1/exotel/dtmf` | Farmer presses a key |
| `POST` | `/api/v1/exotel/voice` | Audio recording available |
| `POST` | `/api/v1/exotel/hangup` | Call ends |
| `GET`  | `/api/v1/exotel/health` | Credential / connectivity check |

---

## DTMF Menu

Reuses the existing `ivr_flow.py` MAIN_MENU state:

| Key | Action |
|-----|--------|
| 1 | Government schemes |
| 2 | Weather forecast |
| 3 | Market prices |
| 4 | Crop disease help |
| 5 | Request callback |
| 9 | Repeat last prompt |

---

## Environment Variables

Add these to your `.env` file:

```env
# Exotel — Sprint 29 IVR demo
EXOTEL_SID=your_exotel_account_sid
EXOTEL_TOKEN=your_exotel_api_token
EXOTEL_PHONE=your_virtual_exophone_number
```

> **No credentials are hardcoded.** All values are read from `settings`.

---

## Exotel Dashboard Setup

1. Log in to [Exotel Dashboard](https://app.exotel.com)
2. Go to **App Bazaar → My Apps → Create App**
3. Create a **Passthru** app with:
   - **Inbound URL**: `https://<your-domain>/api/v1/exotel/inbound`
   - **DTMF fallback URL**: `https://<your-domain>/api/v1/exotel/dtmf`
   - **Hangup URL**: `https://<your-domain>/api/v1/exotel/hangup`
4. Assign the app to your ExoPhone
5. Call the ExoPhone number — Kisan Mitra answers

---

## Mission Control Events

| WebSocket Event | Trigger |
|----------------|---------|
| `CALL_STARTED` | Inbound webhook received |
| `CALLER_IDENTIFIED` | Farmer profile matched |
| `SCHEME_SEARCH_STARTED` | DTMF 1 pressed |
| `SCHEME_MATCHED` | Scheme found |
| `TRANSCRIPT_UPDATED` | STT complete |
| `CALL_COMPLETED` | Hangup received |

All events fire inside the existing `CallManager` — no extra wiring needed.

---

## Post-Call SMS

Automatically triggered by `CallManager` when the call reaches the `SUMMARY`
state. Sent via the SMS Platform (Sprint 28). Contains:

- Conversation summary
- Eligible government schemes
- Recommended actions

---

## Testing

```bash
pytest backend/tests/test_exotel.py -vv
# 3 passed
```

| Test | Coverage |
|------|---------|
| `test_inbound_webhook` | POST `/inbound` → session created, ExoML returned |
| `test_dtmf_webhook` | DTMF digit routed to IVR, ExoML returned |
| `test_sms_after_call` | EXIT state triggers SMS pipeline |

---

## Verification

```bash
ruff check backend/app/ivr/telephony/ backend/tests/test_exotel.py
# → All checks passed!

mypy backend/app/ivr/telephony/ backend/tests/test_exotel.py
# → Success: no issues found in 5 source files
```
