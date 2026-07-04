# Kisan Mitra AI — Demo & Sandbox Guide

This guide describes how to run pilot demonstrations and test sandbox simulations using prepopulated sample data.

---

## 1. Resetting and Seeding Sandbox Data

To ensure a clean environment for demonstration, run the standalone seeder script:
```bash
python scripts/seed_demo.py
```
This script will recreate the local file-based database folder structure and populate it with three diverse sandbox farmer profiles:

| Farmer ID | Name | Preferred Language | Risk Tolerance | Budget Limit | Primary Crop | Location |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `farmer_ramesh` | Ramesh Singh | Hindi (`hi`) | Medium | 150,000 INR | Wheat | Ludhiana, Punjab |
| `farmer_siddappa` | Siddappa Gowda | Kannada (`kn`) | Low | 120,000 INR | Rice | Dharwad, Karnataka |
| `farmer_laxmi` | Laxmi Devi | Telugu (`te`) | Low | 80,000 INR | Cotton | Adilabad, Telangana |

---

## 2. Interactive Demo Queries & Scenarios

### Scenario A: High-Yield Advisory (Ramesh Singh)
1. Query the reasoning platform using Ramesh's ID:
   ```json
   {
     "query": "When should I apply urea fertilizer to my wheat crop?",
     "farmer_id": "farmer_ramesh",
     "language": "hi"
   }
   ```
2. Verify the output advisory:
   * Translates advice to Hindi.
   * Incorporates Ramesh's Digital Twin details (Ludhiana soil Medium Nitrogen levels).
   * Appends memory references of past Yellow Rust issues.

### Scenario B: Low-Risk Adaptation (Siddappa Gowda)
1. Query the reasoning platform using Siddappa's ID:
   ```json
   {
     "query": "How can I maximize rice yields within a strict budget?",
     "farmer_id": "farmer_siddappa",
     "language": "kn"
   }
   ```
2. Verify the output:
   * Restricts recommended chemical fertilizer brands to low-cost alternatives.
   * Leverages canal irrigation history details from Siddappa's Digital Twin.

---

## 3. Telemetry Visualizer Sandbox

1. Open the UI browser page.
2. Select the **AI Specialist Hub** tab.
3. Observe live indicators:
   * Total tokens generated, USD costs, and active fallback models.
   * Trigger mock failovers by temporarily deleting API keys in settings to observe seamless cloud-to-local fallback execution.
