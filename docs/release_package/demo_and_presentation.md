# Kisan Mitra AI — Judge Demo Script & Technical PPT Outline

This document combines the interactive presentation script for hackathon judges and a slide-by-slide technical presentation outline.

---

## 1. Judge Demo Script (7-Minute Presentation)

### **Slide 0: Landing (0:00 - 0:45)**
*Visual*: Mission Control Dashboard showing connection state "Live Connected (1)".
- **Narrator**: "Welcome, Judges. Today, we are presenting Kisan Mitra AI, a multi-agent welfare eligibility platform. Our mission is to bridge the last-mile gap in rural welfare access using voice intelligence."

### **Slide 1: Problem (0:45 - 1:30)**
*Visual*: Digital twin panel in dormant state.
- **Narrator**: "India allocates thousands of crores for rural subsidies annually. However, because rules are complex and internet access is limited, smallholder farmers struggle to check their eligibility. Kisan Mitra AI resolves this by connecting simple keypad phones to an AI eligibility engine."

### **Slide 2: Live Demo - Identification (1:30 - 3:00)**
*Visual*: Select 'Ramesh Singh' from dropdown and click 'Simulate Call'.
- **Narrator**: "Watch the dashboard. We trigger a call simulation. The **Workflow Stage Canvas** immediately responds: Call Started → Caller Identified → Digital Twin Loaded. The system retrieves Ramesh's profile: a small farmer from Ludhiana, Punjab, farming 2 hectares of wheat."

### **Slide 3: Eligibility & Reasoning (3:00 - 5:00)**
*Visual*: Schemes evaluation cards sliding in, PM-KISAN showing green status.
- **Narrator**: "Now, the **Government Schemes Engine** evaluates all 11 schemes. Ramesh is marked `ELIGIBLE` for **PM-KISAN** because his land size is under the 2.0-hectare limit. The **Chief Reasoning Engine** displays the step-by-step logic trail, giving complete explainability."

### **Slide 4: Document Checklist & TTS (5:00 - 6:00)**
*Visual*: Required documents display Aadhaar, Land Records, Bank details.
- **Narrator**: "The **Document Advisor** compiles a checklist showing available vs missing documents. It locates his nearest office: *District Agriculture Office, Civil Lines, Ludhiana*. The voice summary is prepared in Punjabi, instructing him on next steps."

### **Slide 5: Wrap-up & Q&A (6:00 - 7:00)**
*Visual*: Event Stream showing all 13 pipeline events successfully completed.
- **Narrator**: "Kisan Mitra AI is optimized for performance, with the logic engine executing in under 10ms. All 252 quality gate tests pass. We are open for questions."

---

## 2. Technical PPT Outline (10-Slide Deck)

### **Slide 1: Title Slide**
- **Title**: Kisan Mitra AI: Voice-Driven Government Scheme Intelligence for Rural Farmers
- **Subtitle**: Multi-Agent Orchestration & Explainable Eligibility

### **Slide 2: The Welfare Access Gap**
- **Key Points**:
  - Fragmented eligibility rules across state/central registries.
  - Internet access limitations for smallholder rural farmers.
  - Overburdened rural counseling desks.

### **Slide 3: High-Level Architecture**
- **Key Points**:
  - Telephony IVR Layer (button-phone compatible).
  - FastAPI backend routers and Next.js operations dashboard.
  - Databases: PostgreSQL, Redis session cache, and ChromaDB vector store.

### **Slide 4: Multi-Agent Advisory Graph**
- **Key Points**:
  - Graph Orchestrator led by a central Planner Agent.
  - Specialist Agents: Weather, Market Mandi, Government Schemes, Memory, Verifier.
  - Multi-agent collaboration to construct personal advice profiles.

### **Slide 5: Explainable Eligibility Engine**
- **Key Points**:
  - Rule-based calculations for 11 core schemes.
  - Verifiable reasoning chains (e.g. land size, state boundaries, gender).
  - Diagnostic transparency (rejects black-box AI outputs for regulatory compliance).

### **Slide 6: Mission Control Operations Dashboard**
- **Key Points**:
  - Dynamic WebSockets live stream connection (`/ws/live`).
  - 9-Stage Workflow Canvas tracking E2E call checkpoints.
  - Digital twin snapshots and progressive scheme evaluation.

### **Slide 7: Latency & Performance Specs**
- **Key Points**:
  - Engine evaluation latency: < 10ms.
  - Total call simulation pipeline: ~1.2s.
  - Backend footprint: ~85MB RAM at idle.
  - Optimized static page bundle size: Under 180 KB.

### **Slide 8: Production Security & Compliance**
- **Key Points**:
  - Credentials isolation using settings loaders.
  - Rate limiting (MAX_CONNECTIONS=50) on WebSocket pools.
  - DPDP compliance logging rules (unmasked PII scrub filters).

### **Slide 9: Limitations & Roadmap**
- **Key Points**:
  - *Limitations*: Digitized land Bhulekh integration is simulated; TTS readback is mock text.
  - *Roadmap*: Finetuning Indic LLMs; Whatsapp business integrations; live UIDAI e-KYC gateway.

### **Slide 10: Conclusion & Q&A**
- **Key Points**:
  - 252/252 pytest coverage.
  - Scalable container structure.
  - Open for questions.
