# Kisan Mitra AI — Executive Summary & Project Overview

## 1. Executive Summary

### The Challenge
India supports over 140 million farming households, of which more than 80% are small or marginal landowners. The government launches hundreds of welfare schemes and subsidies annually, representing thousands of crores of allocated support. However, due to complex eligibility criteria, fragmented local language documentation, lack of internet access, and overburdened rural counseling desks, a significant volume of this support remains unclaimed. Smallholder farmers are frequently unable to navigate the administrative steps required to confirm eligibility and secure assistance.

### The Solution: Kisan Mitra AI
Kisan Mitra AI is an enterprise-grade, conversational multi-agent platforms that makes government welfare schemes instantly accessible to rural farmers through natural voice interaction. By combining standard telephone networks (IVR) with artificial intelligence, the system allows farmers to dial a number, speak in their native dialect or select options via DTMF keypad, and receive immediate personalized eligibility verdicts and step-by-step application advice.

### System Key Pillars
1. **Multi-Agent Advisory Graph**: A network of specialized AI agents (Weather, Market Mandi, Government Schemes, Memory, and Verification) coordinated by a central Planner Agent.
2. **Explainable Eligibility Engine**: A rule-based calculator that matches farmer profiles against 11 core schemes, providing clear logic trails instead of black-box AI outputs.
3. **Operations Mission Control Dashboard**: A live operations control panel utilizing persistent WebSocket connections to stream call lifecycles, digital twin attributes, and matching processes in real-time.

---

## 2. One-Page Project Overview

| Attribute | Specification Details |
|-----------|-----------------------|
| **Project Title** | Kisan Mitra AI (v1.0 Release Candidate 1) |
| **Mission Objective** | Bridge the last-mile gap in rural welfare access via automated voice intelligence. |
| **Primary Channel** | Telephony IVR (Button-phone friendly, DTMF / voice-driven). |
| **Secondary Channel** | Web Chat Interface & Live Operations Control Center. |
| **Core Technology Stack** | FastAPI (Python), Next.js (TypeScript, React), Redis, PostgreSQL, ChromaDB. |
| **Specialist Agents** | Planner, Weather, Market, Memory, Knowledge, Government Schemes, Verifier. |
| **Government Schemes (11)**| PM-KISAN, PMFBY, PM-KMY, KCC, PMKSY, PKVY, Mahila Kisan, Soil Health Card, PM Fasal Bima, RKVY, NABARD Agri-Clinic. |
| **Security Controls** | Rate limiting (MAX_CONNECTIONS=50), strict CSP, PII logs masking, SQLAlchemy ORM validation. |
| **E2E Latency Profile** | Backend startup: ~1.7s; Logic engine: <10ms; Total call simulation: ~1.2s (Grade A). |
| **Key Limitations** | Simulated digitized land BHULEKH database check; mock TTS voice playback. |
