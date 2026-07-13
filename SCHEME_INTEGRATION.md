# Government Scheme Integration — Sprint 31

This document summarizes the curated government scheme service integrated in Kisan Mitra AI for Sprint 31.

## Overview
Replaces mock responses with structured evaluation logic for six primary Indian agriculture schemes, fully integrated into the existing AI capability tools and IVR routing paths.

---

## Supported Schemes

1. **PM-KISAN** (Pradhan Mantri Kisan Samman Nidhi)
   - Income support of ₹6,000/year.
   - Requires Aadhaar, Bank Passbook, Land Record, Mobile Number.
2. **PMFBY** (Pradhan Mantri Fasal Bima Yojana)
   - Crop insurance protection against damage.
   - Requires Aadhaar, Bank Passbook, Land Record.
3. **KCC** (Kisan Credit Card)
   - Flexible concessional credit/loans at 4%.
   - Requires Aadhaar, Bank Passbook, Land Record.
4. **Soil Health Card**
   - Free soil testing and nutrition reports.
   - Requires Aadhaar, Land Record.
5. **eNAM** (National Agriculture Market)
   - Online bidding and APMC trading integration.
   - Requires Aadhaar, Bank Passbook, Mobile Number.
6. **PKVY** (Paramparagat Krishi Vikas Yojana)
   - Support for organic farming transition.
   - Requires Aadhaar, Land Record, Income Certificate.

---

## Eligibility Matrix

| Scheme | Eligible Status | Land Size | Other Rules |
|---|---|---|---|
| **PM-KISAN** | Eligible | > 0.0 ha | Must own land, cannot be tenant |
| **PMFBY** | Eligible | N/A | Active crops + bank account linked |
| **KCC** | Eligible | N/A | Active crops + bank account + Aadhaar |
| **Soil Health Card** | Eligible | > 0.0 ha | Must possess cultivable land |
| **eNAM** | Eligible | N/A | Linked bank account + Aadhaar KYC |
| **PKVY** | Eligible | >= 0.4 ha | Transitioning to organic farming |

---

## Document Mapping (Task 4)
Only the actual documents required by the target scheme are parsed and returned (restricted strictly to **Aadhaar**, **Bank Passbook**, **Land Record**, **Income Certificate**, **Caste Certificate**, and **Mobile Number**).

---

## AI Integration (Task 5)
The AI Orchestrator matches user intents like `"I need subsidy"`, `"loan help"`, or `"insurance info"` directly to appropriate schemes via the `route_ai_query` tags.

---

## Tests and Verification
- Run test suite: `pytest backend/tests/test_schemes.py -vv` (11 tests passed).
- Linting: `ruff check` (Clean).
- Type Check: `mypy` (Clean).
