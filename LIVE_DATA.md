# Live Weather & Market API Integration — Sprint 30

This document summarizes the live weather and market data services integrated in Kisan Mitra AI for Sprint 30.

## Overview
This platform brings live meteorological forecasts and mandi crop prices to farmers over IVR, SMS, and the Mission Control dashboard using single-provider, zero-abstraction implementations.

---

## Technical Architecture

### Weather Platform (Open-Meteo)
- **Source**: [Open-Meteo API](https://open-meteo.com/) (No API key required).
- **Endpoint**: `https://api.open-meteo.com/v1/forecast` & Geocoding `https://geocoding-api.open-meteo.com/v1/search`
- **Output**: Location, Latitude, Longitude, Temperature (°C), Relative Humidity (%), Rain Probability (%), Wind Speed (km/h), and Weather Condition.
- **Fail-safe**: Graceful fallback to static telemetry or local defaults if geocoding/network timeouts occur.

### Market Platform (Agmarknet)
- **Source**: data.gov.in public Agmarknet API.
- **Endpoint**: `https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070`
- **Fallback**: Curated embedded JSON fallback representing active prices for 15 primary Indian crops.
- **Output**: Commodity Name, Mandi Market, Today's Price, Yesterday's Price, Trend (`up`, `down`, `stable`).

---

## API Endpoints

- `GET /api/v1/live-data/weather?location=Ludhiana` — Retrieves live geocoded weather summaries.
- `GET /api/v1/live-data/market?commodity=Wheat` — Retrieves live commodity prices from the mandi.
- `GET /api/v1/live-data/dashboard` — Live weather + top market prices for the Mission Control dashboard.

---

## IVR and SMS Integration
- **IVR Menu**: Pressing `2` routes to Live Weather; Pressing `3` routes to Live Market Prices. Calls existing TTS dynamically.
- **SMS Alerts**: Reuses the SMS Platform to send summaries to farmers requesting data.

---

## Tests and Verification
- Run test suite: `pytest backend/tests/test_live_data.py -vv` (20 tests passed).
- Linting: `ruff check` (Clean).
- Type Check: `mypy` (Clean).
