# Kisan Mitra AI — Government Schemes Audit & Dataset Matrix

This document provides a factual audit of the 11 government schemes embedded in the Kisan Mitra AI engine. It details the eligibility logic, required documentation, and department mappings, separating production-grade facts from demo constraints.

---

## 1. Schemes Evaluation Matrix

| Scheme ID | Scheme Title | Benefits / Year | Required Documents | Production Registry Source | Dataset Integrity |
|-----------|--------------|-----------------|--------------------|----------------------------|-------------------|
| `pm-kisan` | Pradhan Mantri Kisan Samman Nidhi | INR 6,000 (3 installments) | Aadhaar Card, Land Records, Bank Details | Dept of Agriculture & Farmers Welfare (DA&FW) | **Production-Ready** |
| `pmfby` | Pradhan Mantri Fasal Bima Yojana | Financial crop loss compensation | Aadhaar Card, Land Sowing Proof, Bank Passbook | PMFBY National Portal / DAC&FW | **Production-Ready** |
| `pmkmy` | PM Kisan Maandhan Yojana | INR 3,000/month pension (post age 60) | Aadhaar Card, Savings Bank Details, KCC Card | Ministry of Agriculture / LIC | **Production-Ready** |
| `kcc` | Kisan Credit Card Scheme | Credit loan up to INR 3 Lakh | Aadhaar, Land Records, Bank Details | NABARD / RBI Agricultural Credit | **Production-Ready** |
| `pmksy` | Pradhan Mantri Krishi Sinchayee Yojana | Up to 55% subsidy on micro-irrigation systems | Land Patta, Water source proof, Aadhaar | Ministry of Water Resources / DAC&FW | **Production-Ready** |
| `pkvy` | Paramparagat Krishi Vikas Yojana | Subsidy support of INR 50,000/ha | Organic Land Certificate, Bank Passbook | Organic Farming Portal of India | **Production-Ready** |
| `mahila-kisan` | Mahila Kisan Sashaktikaran Pariyojana | Financial assistance & input subsidies | Gender certificate (female status), Land Record | Dept of Rural Development | **Production-Ready** |
| `soil-health` | Soil Health Card Scheme | Custom fertilizer advice, soil tests | Land details, Aadhaar Card, Mobile | Dept of Agri Research & Education | **Production-Ready** |
| `pm-fasal` | PM Fasal Bima (Non-loanee optional) | Optional crop insurance | Sowing certificate, Tenant agreement, Land Patta | National Insurance Portal | **Production-Ready** |
| `rkvy` | Rashtriya Krishi Vikas Yojana | Farm infrastructure subsidies | Land possession certificate, Project report | State Agriculture Department | **Production-Ready** |
| `nabard-agri` | NABARD Agri-Clinic Business Scheme | Up to 36% startup subsidy | Ag Degree/Diploma certificate, Project report | NABARD Entrepreneurship Portal | **Production-Ready** |

---

## 2. Dynamic Eligibility Logic Parameters

The rule-based decision loops in `EligibilityEngine` process the following parameters:

```
                            ┌────────────────────────┐
                            │    Farmer Profile      │
                            └───────────┬────────────┘
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
      [Land Ownership]               [Gender]                  [Geography]
   - Land Size <= 2.0ha           - Female only             - State matching rules
   - Tenant vs Landowner         (Mahila-Kisan)             (RKVY localized state check)
```

---

## 3. Data Integrity: Demo vs. Production

To maintain transparency, the following criteria highlight the boundary between demo modes and live production systems:

1. **Aadhaar Verification**:
   - *Demo*: Simple validation checks if the `has_aadhaar` boolean is `True`.
   - *Production*: Integrates with UIDAI OAuth e-KYC gateways for biometric or OTP verification.
2. **Landholding Verification**:
   - *Demo*: Land size (in Hectares) is read directly from the Digital Twin model.
   - *Production*: Queries state-level digitized Bhulekh databases (e.g., Punjab Land Records Society, Bhulekh UP API) to verify land coordinates and titles.
3. **Mandi Prices / Agmarknet**:
   - *Demo*: Leverages historical lookup caches for crop prices.
   - *Production*: Calls active Agmarknet REST API endpoints for real-time Mandi market rates.
