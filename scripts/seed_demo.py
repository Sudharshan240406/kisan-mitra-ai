#!/usr/bin/env python3
"""
Kisan Mitra AI - Demo Data Seeder Utility
Generates sandbox farmer profiles, digital twins, and memories for demonstrations.
"""
import os
import json
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "farmers")

def main():
    print("=" * 60)
    print("KISAN MITRA AI - DEMO DATA SEEDER")
    print("=" * 60)
    
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 1. Profiles Data
    profiles = {
        "farmer_ramesh": {
            "farmer_id": "farmer_ramesh",
            "name": "Ramesh Singh",
            "preferred_language": "hi",
            "experience_level": "intermediate",
            "risk_tolerance": "medium",
            "budget_limit": 150000.0,
            "budget_spent": 45000.0,
            "farm_goals": ["Maximize wheat yield", "Install drip irrigation"],
            "preferences": {}
        },
        "farmer_siddappa": {
            "farmer_id": "farmer_siddappa",
            "name": "Siddappa Gowda",
            "preferred_language": "kn",
            "experience_level": "expert",
            "risk_tolerance": "low",
            "budget_limit": 120000.0,
            "budget_spent": 60000.0,
            "farm_goals": ["Optimize rice irrigation", "Organic soil conditioning"],
            "preferences": {}
        },
        "farmer_laxmi": {
            "farmer_id": "farmer_laxmi",
            "name": "Laxmi Devi",
            "preferred_language": "te",
            "experience_level": "beginner",
            "risk_tolerance": "low",
            "budget_limit": 80000.0,
            "budget_spent": 10000.0,
            "farm_goals": ["Pest control in cotton", "Apply Soil Health Card tips"],
            "preferences": {}
        }
    }
    
    # 2. Digital Twin Details
    twins = {
        "farmer_ramesh": {
            "farmer_id": "farmer_ramesh",
            "land_size_acres": 5.0,
            "village": "Kila Raipur",
            "district": "Ludhiana",
            "state": "Punjab",
            "climate_zone": "Trans-Gangetic Plains",
            "crop_zone": "Wheat-Rice Zone",
            "crop_history": [
                {"crop": "wheat", "season": "Rabi", "year": 2025, "yield_tonnes": 5.2},
                {"crop": "rice", "season": "Kharif", "year": 2025, "yield_tonnes": 4.8}
            ],
            "soil_history": [
                {"ph": 6.8, "nitrogen": "medium", "phosphorus": "medium", "potassium": "high", "tested_at": time.time() - 30 * 86400}
            ],
            "equipment": ["Tractor", "Seed Drill"],
            "livestock": ["Cows (2)"],
            "irrigation_type": "tube_well",
            "scheme_history": ["PM-Kisan", "PMFBY"]
        },
        "farmer_siddappa": {
            "farmer_id": "farmer_siddappa",
            "land_size_acres": 3.5,
            "village": "Heggeri",
            "district": "Dharwad",
            "state": "Karnataka",
            "climate_zone": "Southern Plateau and Hills",
            "crop_zone": "Rice Zone",
            "crop_history": [
                {"crop": "rice", "season": "Kharif", "year": 2025, "yield_tonnes": 4.1}
            ],
            "soil_history": [
                {"ph": 6.2, "nitrogen": "low", "phosphorus": "high", "potassium": "medium", "tested_at": time.time() - 60 * 86400}
            ],
            "equipment": ["Power Tiller"],
            "livestock": ["Buffaloes (3)"],
            "irrigation_type": "canal",
            "scheme_history": ["PM-Kisan"]
        },
        "farmer_laxmi": {
            "farmer_id": "farmer_laxmi",
            "land_size_acres": 2.0,
            "village": "Adilabad Rural",
            "district": "Adilabad",
            "state": "Telangana",
            "climate_zone": "Semi-Arid Zone",
            "crop_zone": "Cotton-Jowar Zone",
            "crop_history": [
                {"crop": "cotton", "season": "Kharif", "year": 2025, "yield_tonnes": 1.8}
            ],
            "soil_history": [
                {"ph": 7.5, "nitrogen": "medium", "phosphorus": "low", "potassium": "medium", "tested_at": time.time() - 15 * 86400}
            ],
            "equipment": [],
            "livestock": ["Oxen (2)"],
            "irrigation_type": "rainfed",
            "scheme_history": ["PM-Kisan", "Rythu Bandhu"]
        }
    }
    
    # 3. Memory Logs
    memories = {
        "farmer_ramesh": {
            "farmer_id": "farmer_ramesh",
            "conversations": [
                {"timestamp": time.time() - 5000, "query": "When should I sow wheat?", "response": "Sow wheat during mid-November."}
            ],
            "recommendations": [
                {"recommendation_id": "REC-RAM-01", "text": "Apply Urea fertilizer in wheat crop", "feedback": "good", "timestamp": time.time() - 10000}
            ],
            "diseases": [{"disease": "Yellow Rust", "date": "2025-02-10"}],
            "weather_events": [{"event": "Delayed Monsoon", "date": "2025-07-01"}],
            "market_decisions": [{"commodity": "wheat", "price": 2275.0, "mandi": "Ludhiana Mandi", "date": "2025-05-15"}],
            "feedback_history": [{"recommendation_id": "REC-RAM-01", "score": 5, "comment": "Wheat crop yields increased by 10%!"}],
            "ai_confidence_history": [0.85, 0.90],
            "historical_outcomes": [{"year": 2025, "net_profit_inr": 85000.0}]
        },
        "farmer_siddappa": {
            "farmer_id": "farmer_siddappa",
            "conversations": [
                {"timestamp": time.time() - 8000, "query": "What fertilizer is best for rice?", "response": "NPK 15:15:15 complex fertilizer."}
            ],
            "recommendations": [
                {"recommendation_id": "REC-SID-01", "text": "Apply Zinc sulphate to rice crop", "feedback": "good", "timestamp": time.time() - 15000}
            ],
            "diseases": [{"disease": "Rice Blast", "date": "2025-09-05"}],
            "weather_events": [{"event": "Dry Spell", "date": "2025-08-12"}],
            "market_decisions": [{"commodity": "rice", "price": 2100.0, "mandi": "Dharwad Mandi", "date": "2025-10-01"}],
            "feedback_history": [{"recommendation_id": "REC-SID-01", "score": 4, "comment": "Yellowing of leaves stopped after Zinc application"}],
            "ai_confidence_history": [0.82, 0.88],
            "historical_outcomes": [{"year": 2025, "net_profit_inr": 62000.0}]
        },
        "farmer_laxmi": {
            "farmer_id": "farmer_laxmi",
            "conversations": [
                {"timestamp": time.time() - 12000, "query": "How to treat bollworms in cotton?", "response": "Use neem oil spray or pheromone traps."}
            ],
            "recommendations": [
                {"recommendation_id": "REC-LAX-01", "text": "Set up pheromone traps for pink bollworm", "feedback": "good", "timestamp": time.time() - 20000}
            ],
            "diseases": [{"disease": "Pink Bollworm", "date": "2025-08-20"}],
            "weather_events": [],
            "market_decisions": [],
            "feedback_history": [{"recommendation_id": "REC-LAX-01", "score": 5, "comment": "Bollworm infestation fully controlled."}],
            "ai_confidence_history": [0.88],
            "historical_outcomes": [{"year": 2025, "net_profit_inr": 42000.0}]
        }
    }
    
    # 4. Consent Profiles
    consents = {
        "farmer_ramesh": {
            "farmer_id": "farmer_ramesh",
            "consent_given": True,
            "data_retention_days": 365,
            "memory_controls": {},
            "personalization_settings": {},
            "privacy_preferences": {}
        },
        "farmer_siddappa": {
            "farmer_id": "farmer_siddappa",
            "consent_given": True,
            "data_retention_days": 365,
            "memory_controls": {},
            "personalization_settings": {},
            "privacy_preferences": {}
        },
        "farmer_laxmi": {
            "farmer_id": "farmer_laxmi",
            "consent_given": True,
            "data_retention_days": 365,
            "memory_controls": {},
            "personalization_settings": {},
            "privacy_preferences": {}
        }
    }
    
    # 5. Reminders Data
    reminders = {
        "farmer_ramesh": [
            {
                "reminder_id": "REM-RAM-01",
                "farmer_id": "farmer_ramesh",
                "type": "fertilizer",
                "message": "Time to apply second dose of Nitrogen fertilizer on Wheat crop.",
                "due_date": time.time() + 86400 * 3,
                "status": "pending",
                "priority": "high",
                "created_at": time.time()
            }
        ],
        "farmer_siddappa": [
            {
                "reminder_id": "REM-SID-01",
                "farmer_id": "farmer_siddappa",
                "type": "irrigation",
                "message": "Check canal water release timing and irrigate rice field.",
                "due_date": time.time() + 86400 * 2,
                "status": "pending",
                "priority": "medium",
                "created_at": time.time()
            }
        ],
        "farmer_laxmi": [
            {
                "reminder_id": "REM-LAX-01",
                "farmer_id": "farmer_laxmi",
                "type": "disease_monitoring",
                "message": "Check cotton plant leaves for whiteflies activity.",
                "due_date": time.time() + 86400 * 5,
                "status": "pending",
                "priority": "medium",
                "created_at": time.time()
            }
        ]
    }
    
    # Write files
    def write_json(filename, data):
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[+] Seeded file: {filepath}")

    write_json("profiles.json", profiles)
    write_json("twins.json", twins)
    write_json("memories.json", memories)
    write_json("consents.json", consents)
    write_json("reminders.json", reminders)
    
    print("[+] Seeding complete! Demo data is ready for pilot run.")
    print("=" * 60)

if __name__ == "__main__":
    main()
