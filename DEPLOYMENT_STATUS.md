# Deployment Status — Kisan Mitra AI

This document outlines the current deployment status, missing requirements, and necessary actions to launch Kisan Mitra AI.

---

## 1. Status Summary

- **Backend Public URL**: None
- **Frontend Public URL**: None
- **Deployment Status**: **PENDING (Missing Cloud Account Credentials / API Tokens)**

---

## 2. Missing Credentials & secrets
To complete the production deployment, the following credentials must be configured:

1. **Deployment Platform Secrets (for CLI/CI deployment)**:
   - **Render / Railway API Token** (needed to deploy backend service and database via CLI).
   - **Vercel Auth Token / CLI login** (needed to deploy the Next.js frontend).
2. **Third-Party Telephony & SMS Integrations**:
   - **Exotel Account SID & API Token**: Required to receive and process inbound telephony calls.
   - **Plivo / Twilio Credentials**: Required to dispatch post-call SMS summaries to farmers.
3. **AI Orchestrator**:
   - **Gemini API Key**: Required for natural language parsing and intent generation.

---

## 3. Remaining Manual Steps

To deploy Kisan Mitra AI manually, perform the following steps:

### Step 1: Deploy Backend (Render)
1. Go to [Render](https://render.com/).
2. Create a new **Web Service** and link the `kisan-mitra-ai` repository.
3. Set the Root Directory to `backend`.
4. Choose **Docker** as the environment (Render will read `backend.Dockerfile` from the `deployment/docker` path automatically if specified, or you can build from source using python `requirements.txt`).
5. Configure the Environment Variables listed in `DEPLOYMENT_GUIDE.md` (e.g. `GEMINI_API_KEY`, `EXOTEL_SID`, etc.).
6. Click **Deploy**. Note the generated backend URL (e.g., `https://kisan-mitra-api.onrender.com`).

### Step 2: Deploy Frontend (Vercel)
1. Go to [Vercel](https://vercel.com/).
2. Import the `kisan-mitra-ai` repository.
3. Set the Root Directory to `frontend`.
4. Set the build command to `npm run build`.
5. Add the Environment Variable:
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: `https://your-backend-url.onrender.com`
6. Click **Deploy**. Note the generated frontend URL.
