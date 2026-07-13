# Deployment & Demo Validation Guide — Sprint 32

This guide outlines deployment steps, environment configurations, and validation flows for deploying **Kisan Mitra AI** (Backend + Frontend) in a production environment.

---

## 1. Backend Deployment (Render or Railway)

### Deployment Options
1. **Docker Deployment (Recommended)**: Use the provided [backend.Dockerfile](file:///c:/Users/Admin/Desktop/kisan-mitra-ai/deployment/docker/backend.Dockerfile).
2. **Native Python Deployment**: Start the server using virtualenv with Python 3.11+.

### Render Configurations
- **Service Type**: Web Service
- **Environment**: Docker (or Python)
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/health`

### Environment Variables
Configure the following keys in your backend settings:
```env
# Platform & Credentials
APP_ENV=production
DEBUG=false
FEATURE_LLM_ENABLED=true
DEFAULT_LLM_PROVIDER=gemini       # Options: gemini, openai, claude, mock
GEMINI_API_KEY=your_gemini_api_key

# Exotel Telephony Webhook (Sprint 29)
EXOTEL_SID=your_exotel_account_sid
EXOTEL_TOKEN=your_exotel_api_token
EXOTEL_PHONE=your_virtual_exophone_number

# SMS Platform (Sprint 28)
SMS_PROVIDER=mock                # Options: mock, twilio, plivo
PLIVO_AUTH_ID=your_plivo_auth_id
PLIVO_AUTH_TOKEN=your_plivo_auth_token
PLIVO_PHONE_NUMBER=your_plivo_phone_number
```

---

## 2. Frontend Deployment (Vercel)

### Deployment Command
Deploy the `frontend/` folder directly to Vercel:
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Root Directory**: `frontend`

### Environment Variables
You MUST define the backend API URL for Next.js to target during compilation:
- **`NEXT_PUBLIC_API_URL`**: `https://your-backend-url.onrender.com` (no trailing slash).

---

## 3. End-to-End Demo Call Flow Validation

Once deployed, follow these steps to verify the entire system:

1. **Verify Mission Control**:
   - Navigate to the frontend homepage.
   - Open **Mission Control Dashboard** to verify WebSocket listener connectivity.
2. **Initiate Phone Call**:
   - Dial your virtual Exotel phone number (`EXOTEL_PHONE`).
   - Confirm Kisan Mitra AI picks up the call and plays the multilingual greeting menu.
3. **Select Menu Options**:
   - Press **`1`** for Government Schemes (evaluated live by the new `SchemeService` for PM-KISAN, PMFBY, KCC, Soil Health Card, eNAM, PKVY).
   - Press **`2`** for Weather forecast (pulled live from Open-Meteo).
   - Press **`3`** for Mandi Market prices (pulled live from Agmarknet/Curated database).
4. **Speak Question (Voice/STT)**:
   - Speak a question (e.g. asking about organic subsidies).
   - The STT platform transcribes the question and feeds it into the AI Orchestrator.
5. **TTS Playback**:
   - The system synthesizes the AI response into speech and plays it back to the farmer over the phone.
6. **Post-Call SMS Summary**:
   - Hang up.
   - Confirm that a comprehensive SMS summary is automatically dispatched to the farmer's mobile number.
7. **Mission Control Updates**:
   - Check the dashboard; confirm `CALL_STARTED`, `CALLER_IDENTIFIED`, and `CALL_COMPLETED` events are displayed in real-time.
