# Kisan Mitra AI — Hackathon Demonstration Guide & Judge Script

Welcome to the hackathon demonstration guide for Kisan Mitra AI. This guide provides a 7-minute judge script, expected workflow checkpoints, and backup demo flows.

---

## 1. 7-Minute Walkthrough Timing Breakdown

| Stage | Duration | Presenter Objective | Dashboard Reaction |
|-------|----------|---------------------|--------------------|
| **1. Hook & Overview** | 1.0 min | Pitch the problem of access to government welfare for marginalized farmers. | Landing page of Mission Control tab showing "Ready" connection. |
| **2. Interactive Flow Setup** | 1.5 min | Introduce the caller identity database. Highlight 6 diverse farmer archetypes from different states. | Dropdown select box populated with the 6 profiles. |
| **3. Live Call Simulation** | 2.0 min | Simulate a phone query for Ramesh Singh (Small landowner, Punjab). Run the E2E pipeline. | Canvas lights up: Call Started → Caller ID → Twin Loaded. |
| **4. Live Analytics & Reasoning** | 1.5 min | Showcase explainable eligibility check for the 11 schemes and Chief Reasoning outputs. | Match cards stream live one-by-one. Top scheme (PM-KISAN) displays logic. |
| **5. Document Advisory** | 1.0 min | Show targeted checklist mapping missing docs and localized Tehsildar office details. | Documents list dynamically reveals required vs missing items. |

---

## 2. Complete Judge Walkthrough Script

### **Stage 1: Hook (Minutes 0:00 - 1:00)**
> "Judges, out of 140 million farmers in India, over 80% are small or marginal. Every year, thousands of crores of government welfare remain unspent because eligibility rules are fragmented, documents are hard to verify, and call centers are overwhelmed.
> 
> Introducing Kisan Mitra AI: a fully explainable, multi-agent government scheme intelligence platform. Through a simple button-phone IVR call, our system translates spoken dialect, resolves a farmer's identity to a Digital Twin, matches eligibility rules in real-time, and issues localized application instructions."

### **Stage 2: Setup (Minutes 1:00 - 2:30)**
> "Let's look at our Live Operations Mission Control dashboard. The backend is connected directly via high-frequency WebSockets.
> 
> Under the hood, our platform maintains a farmer database. We have pre-loaded six realistic, highly diverse profiles representing small, marginal, organic, and tenant farmers across Punjab, Rajasthan, Maharashtra, and Karnataka.
> 
> Let's select **Ramesh Singh** from Ludhiana, Punjab. Ramesh is a small landowner growing wheat and rice on 2 hectares."

### **Stage 3: Pipeline Execution (Minutes 2:30 - 4:30)**
> "We click 'Simulate Call'. Notice the Workflow Stage Canvas immediately animating:
> - **Call Started** detects incoming metadata.
> - **Caller ID** maps the phone to Ramesh's profile.
> - **Digital Twin Loaded** pulls Ramesh's details, risk profile, and profile completeness.
> 
> Now, the **Scheme Search** begins. The engine evaluates all 11 core agricultural schemes. See them match live in real-time. Each scheme is graded: Eligible, Possibly Eligible, or Not Eligible.
> 
> Ramesh passes **PM-KISAN** (Pradhan Mantri Kisan Samman Nidhi) because his land size is under the 2.0-hectare ceiling. He fails **Mahila Kisan** because of gender criteria. Every verdict is explainable."

### **Stage 4: Reasoning & Documents (Minutes 4:30 - 6:00)**
> "Look at the Chief Reasoning Agent panel. It outputs Ramesh's exact decision logs:
> `✓ passes Land Size Limit <= 2.0ha (2.0ha verified)`
> `✓ passes Active Landownership`
> 
> The **Document Advisor** checklist immediately compiles. It displays which documents are already available vs missing (such as landholder records). It locates his nearest office: *District Agriculture Office, Civil Lines, Ludhiana* and provides the direct helpline.
> 
> Finally, the TTS Voice Summary output shows the actual spoken advice translated to Ramesh's preferred language (Punjabi/Hindi), giving him clear instructions."

### **Stage 5: Wrap-up & Q&A (Minutes 6:00 - 7:00)**
> "Kisan Mitra AI is ready to scale. It integrates easily with IVR providers, handles error states gracefully, and resolves eligibility instantly. We are open for questions."

---

## 3. Multilingual Translation & Intent Matrix

When demoing different farmers, verify the following inputs/outputs:

| Farmer | Selected Language | Expected Top Scheme | Speech Intros | Localized Office |
|--------|-------------------|---------------------|---------------|------------------|
| **Ramesh Singh** | Punjabi (`pa`) / Hindi (`hi`) | PM-KISAN | *"नमस्ते रमेश सिंह..."* | Ludhiana, Civil Lines |
| **Lakshmi Devi** | Hindi (`hi`) | Mahila Kisan | *"नमस्ते लक्ष्मी देवी..."* | Jaipur, Krishi Bhawan |
| **Priya Kumari** | English (`en`) | PKVY Organic | *"Hello Priya Kumari..."* | Bangalore, RCOF |
| **Mohammed Rafi** | English (`en`) | PMFBY Crop Insurance | *"Hello Mohammed Rafi..."* | Nagpur, Civil Lines |

---

## 4. Error Recovery Demo Flow

To demonstrate the robustness of the system to judges, you can simulate a failure:
1. **Invalid Farmer Selection**: Post a payload with a non-existent farmer ID to the simulate endpoint.
2. **Dashboard Reaction**:
   - The status lights up in red **ERROR**.
   - The timeline logs a `CALL_ERROR` event.
   - The **TTS Voice Summary** displays a fallback message in Hindi directing the caller to dial the national agriculture helpline `1800-180-1551`.

---

## 5. Backup Offline Walkthrough Mode

If uvicorn or next.js has local execution problems during the presentation:
1. Open the pre-generated integration test reports (see `C:/Users/Admin/Desktop/kisan-mitra-ai/walkthrough.md`).
2. Run the mock server output showing the 252 successful pytests.
3. Show static screenshots of the Mission Control interface (located under frontend components).
