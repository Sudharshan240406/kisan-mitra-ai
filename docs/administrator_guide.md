# Kisan Mitra AI — Administrator Guide

This guide is designed for administrators, system operators, and NGO deployment leads. It explains how to check platform health, modify configurations, tail logs, and toggle external API adapters.

---

## 1. Administrative API Endpoints

The backend exposes primary endpoints under `/api/v1/admin` to audit the live server state:

### GET `/api/v1/admin/config`
Retrieves settings, API endpoints, active integration adapters, and daily LLM spending budget limits:
```json
{
  "app_name": "KisanMitraAI",
  "environment": "production",
  "debug_mode": false,
  "active_llm_provider": "gemini",
  "sms_provider": "twilio",
  "integration_active_mappings": {
    "weather": "tomorrow-io",
    "market": "agmarknet"
  },
  "budget_limits": {
    "daily_usd_budget": 5.0,
    "accumulated_cost_usd": 0.125
  }
}
```

### GET `/api/v1/admin/stats`
Compiles live system diagnostics, registered agents, vector DB connectivity, and memory usage metrics:
```json
{
  "onboarded_farmers_count": 3,
  "total_conversation_memories": 8,
  "total_scheduled_reminders": 3,
  "registered_agents": ["Planner", "Weather", "Market", "Memory", "Knowledge", "GovernmentScheme", "Verifier"]
}
```

### GET `/api/v1/admin/logs`
Tails the last N lines of application (`logs/app.log`) or error (`logs/error.log`) files:
* Query parameters: `lines` (default 100), `log_type` (`app` | `error`).

---

## 2. Integration Provider Management

The platform supports live swapping of primary API integrations. If an adapter experiences issues or API keys expire:
1. **List Integrations**: Call `GET /api/v1/integrations` to list all adapters and see which one is active.
2. **Activate Primary Provider**: Call `POST /api/v1/integrations/{integration_id}/activate` to immediately route queries to the new primary provider (e.g. swap weather from `imd-weather` to `tomorrow-io`).
3. **Toggle Status**: Call `POST /api/v1/integrations/{integration_id}/toggle` to enable/disable an adapter.
4. **Test Run**: Call `POST /api/v1/integrations/{integration_id}/test` to trigger a safe test transaction to measure adapter latency and verify credentials.

---

## 3. Dynamic Feature Flags

Feature flags are loaded from environment settings at startup:
* `FEATURE_VOICE_ENABLED`: Enables/disables speech transcription and TTS voice synthesis.
* `FEATURE_SMS_ENABLED`: Toggles outgoing SMS text notifications.
* `FEATURE_REASONING_ENABLED`: Toggles multi-agent reasoning graphs execution.
* Adjust environment flags inside docker compose `.env` files to scale operations.
