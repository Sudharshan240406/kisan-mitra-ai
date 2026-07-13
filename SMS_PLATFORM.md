# SMS Platform — Sprint 28

> **Kisan Mitra AI** — Production-ready SMS layer for farmer communication.

---

## Overview

The SMS Platform enables Kisan Mitra to communicate with farmers through SMS for:

- 📲 **Post-call summaries** — Automatically sent after every IVR call
- 🌾 **Scheme alerts** — Government scheme notifications
- 🌦️ **Weather reminders** — Upcoming weather warnings
- 📈 **Market price updates** — Crop price alerts
- 🔐 **OTP delivery** — Authentication one-time passwords
- 💬 **Two-way conversations** — Inbound SMS routed to AI Orchestrator

---

## Architecture

```
backend/app/sms/
├── __init__.py             # Package exports
├── provider_base.py        # Base enums, schemas & Protocol interface
├── provider_registry.py    # Dynamic provider registry with health checks
├── twilio_provider.py      # Twilio SMS integration (primary)
├── msg91_provider.py       # MSG91 SMS integration (India-optimised)
├── exotel_provider.py      # Exotel SMS integration (IVR-native)
├── fallback_provider.py    # Local stub fallback (dev / resilience)
├── template_engine.py      # Versioned, multilingual template rendering
├── sms_manager.py          # Core coordinator — dispatch, retry, telemetry
└── inbound_router.py       # Two-way inbound SMS → AI Orchestrator routing
```

---

## Components

### `provider_base.py`

Defines shared contracts used by every provider:

| Symbol | Kind | Purpose |
|---|---|---|
| `SMSStatus` | Enum | `SENT`, `DELIVERED`, `FAILED`, `QUEUED`, `PENDING` |
| `SMSProviderStatus` | Enum | `ACTIVE`, `INACTIVE`, `ERROR`, `DEGRADED` |
| `SMSMetadata` | Pydantic model | Delivery metadata attached to every dispatch |
| `SMSMessage` | Pydantic model | Complete SMS envelope (recipient, body, priority, language) |
| `BaseSMSProvider` | Protocol | Structural interface all providers must satisfy |

---

### `provider_registry.py`

Dynamic registry that holds named provider instances:

| Method | Description |
|---|---|
| `register(provider)` | Register a named provider |
| `set_active(name)` | Mark a provider as the primary sender |
| `get_active()` | Retrieve current active provider |
| `list_providers()` | All registered provider names |
| `health_check_all()` | Async health probe across all providers |

---

### SMS Providers

| Provider | Class | Notes |
|---|---|---|
| Twilio | `TwilioProvider` | Primary — uses `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_PHONE_NUMBER` |
| MSG91 | `MSG91Provider` | India-optimised transactional & OTP SMS |
| Exotel | `ExotelProvider` | IVR-native telephony provider for rural India |
| Fallback | `FallbackProvider` | Logs locally — dev environments & resilience chain |

All providers expose a common interface:

```python
async def send_sms(recipient: str, body: str) -> bool: ...
async def health_check() -> bool: ...
```

---

### `template_engine.py`

Versioned, language-aware template renderer:

**Supported languages**

| Code | Language |
|---|---|
| `en` | English |
| `hi` | Hindi |
| `kn` | Kannada |
| `te` | Telugu |
| `ta` | Tamil |

**Template types**

| Key | Use-case |
|---|---|
| `welcome` | First contact greeting |
| `call_summary` | Post-IVR call digest |
| `scheme_alert` | Government scheme notification |
| `weather_alert` | Weather warning |
| `market_price` | Crop price update |
| `otp` | Authentication OTP |
| `reminder` | General reminder |

**Usage**

```python
engine = TemplateEngine()
msg = engine.render("call_summary", language="hi", variables={
    "farmer_name": "Ramesh",
    "summary": "आपकी फसल की बात हुई।",
    "schemes": "PM-Kisan",
    "actions": "खाद खरीदें"
})
```

---

### `sms_manager.py`

Core coordinator responsible for the full SMS lifecycle:

1. **Provider selection** — Uses the active provider from the registry
2. **Automatic failover** — Falls back through the provider chain on errors
3. **Retry logic** — Configurable retry count with exponential backoff
4. **Telemetry** — Records dispatch metrics to the observability framework
5. **Mission Control events** — Pushes `SMS_TELEMETRY` WebSocket events

```python
manager = SMSManager(registry)
await manager.send(recipient="+919876543210", body="Your summary...", language="hi")
```

---

### `inbound_router.py`

Handles incoming SMS from farmers:

1. Resolves the farmer profile from the Demo Service
2. Broadcasts `SMS_TELEMETRY` (direction: inbound) to Mission Control
3. Builds a structured `ChannelMessage` envelope
4. Routes the message to the **AI Orchestrator** via `channel_router`
5. Returns the AI response as a reply SMS body

---

## DI Container Integration

The SMS Platform is wired into the container in `backend/app/core/container.py`:

```python
# Providers
self.sms_provider_registry   # ProviderRegistry
self.sms_manager             # SMSManager  
self.sms_inbound_router      # InboundRouter
```

All three are initialised at startup via `_load_default_sms_providers()` which loads Twilio (primary), MSG91, Exotel, and Fallback providers.

---

## IVR Integration

`backend/app/ivr/call_manager.py` automatically sends a post-call summary SMS when a call reaches the `SUMMARY` state:

```
Call ends → SUMMARY state → send_post_call_sms()
```

The SMS includes:
- Call summary narrative
- Active government schemes
- Weather conditions
- Recommended actions

---

## Configuration

| Setting | Description |
|---|---|
| `TWILIO_ACCOUNT_SID` | Twilio account identifier |
| `TWILIO_AUTH_TOKEN` | Twilio authentication token |
| `TWILIO_PHONE_NUMBER` | Outbound sender number |

All settings are read from `backend/app/core/config.py` via `settings.*`.

---

## Testing

```bash
pytest backend/tests/test_sms.py -vv
```

| Test | Coverage |
|---|---|
| `test_sms_providers_instantiation` | All 4 providers instantiate correctly |
| `test_provider_registry_operations` | Register, activate, list, health-check |
| `test_template_engine_substitutions` | English & Hindi template rendering |
| `test_sms_manager_fallback_and_retry` | Failover chain on primary failure |
| `test_inbound_router_two_way_flow` | Inbound SMS → AI Orchestrator routing |
| `test_ivr_summary_auto_sms` | Post-call SMS triggered automatically |

---

## Verification

```bash
# Lint
ruff check backend/app/sms/ backend/tests/test_sms.py
# → All checks passed!

# Types
mypy backend/app/sms/ backend/tests/test_sms.py
# → Success: no issues found in 16 source files

# Tests
pytest backend/tests/test_sms.py backend/tests/test_stt.py \
       backend/tests/test_tts.py backend/tests/test_ivr.py \
       backend/tests/test_telephony.py
# → 31 passed in 123.53s
```

---

## Sprint Status

✅ **SPRINT 28 — SMS PLATFORM — COMPLETE**
