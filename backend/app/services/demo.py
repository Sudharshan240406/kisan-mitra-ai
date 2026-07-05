"""
Kisan Mitra AI — Demo Farmer Profiles
========================================
Pre-built realistic farmer archetypes for judge demonstration.
Each farmer has a distinct profile that triggers different scheme recommendations.
"""
from __future__ import annotations

import logging
from typing import Any

from app.models.farmer import Farmer

logger = logging.getLogger("kisan_mitra_ai.services.demo")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Demo Farmer Profiles
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEMO_FARMERS: list[Farmer] = [
    Farmer(
        farmer_id="DEMO-F001",
        name="Ramesh Singh",
        phone_number="+919876543210",
        state="Punjab",
        district="Ludhiana",
        preferred_language="pa",
        land_size_hectares=2.0,
        soil_type="Alluvial",
        water_source="Tubewell",
        active_crops=["Wheat", "Rice"],
        farmer_category="Small",
        gender="Male",
        caste_category="General",
        income_bracket="Below 2 Lakh",
        has_bank_account=True,
        has_aadhaar=True,
        crop_season="Rabi",
        is_tenant=False,
        is_organic=False,
        recent_damage=None,
        metadata={"age": 45, "education": "10th pass", "family_size": 5},
    ),
    Farmer(
        farmer_id="DEMO-F002",
        name="Lakshmi Devi",
        phone_number="+919876543211",
        state="Rajasthan",
        district="Jaipur",
        preferred_language="hi",
        land_size_hectares=0.5,
        soil_type="Sandy Loam",
        water_source="Rainfed",
        active_crops=["Mustard", "Bajra"],
        farmer_category="Marginal",
        gender="Female",
        caste_category="OBC",
        income_bracket="Below 1 Lakh",
        has_bank_account=True,
        has_aadhaar=True,
        crop_season="Rabi",
        is_tenant=False,
        is_organic=False,
        recent_damage=None,
        metadata={"age": 38, "education": "5th pass", "family_size": 4, "shg_member": True},
    ),
    Farmer(
        farmer_id="DEMO-F003",
        name="Gopal Yadav",
        phone_number="+919876543212",
        state="Madhya Pradesh",
        district="Indore",
        preferred_language="hi",
        land_size_hectares=1.0,
        soil_type="Black Cotton Soil",
        water_source="Canal",
        active_crops=["Soybean", "Wheat"],
        farmer_category="Small",
        gender="Male",
        caste_category="OBC",
        income_bracket="Below 2 Lakh",
        has_bank_account=True,
        has_aadhaar=True,
        crop_season="Kharif",
        is_tenant=True,
        is_organic=False,
        recent_damage=None,
        metadata={"age": 52, "education": "8th pass", "family_size": 6},
    ),
    Farmer(
        farmer_id="DEMO-F004",
        name="Priya Kumari",
        phone_number="+919876543213",
        state="Karnataka",
        district="Dharwad",
        preferred_language="kn",
        land_size_hectares=3.0,
        soil_type="Red Laterite",
        water_source="Borewell",
        active_crops=["Turmeric", "Groundnut"],
        farmer_category="Medium",
        gender="Female",
        caste_category="General",
        income_bracket="2-5 Lakh",
        has_bank_account=True,
        has_aadhaar=True,
        crop_season="Kharif",
        is_tenant=False,
        is_organic=True,
        recent_damage=None,
        metadata={"age": 34, "education": "Graduate", "family_size": 3, "organic_certified": True},
    ),
    Farmer(
        farmer_id="DEMO-F005",
        name="Mohammed Rafi",
        phone_number="+919876543214",
        state="Maharashtra",
        district="Nagpur",
        preferred_language="hi",
        land_size_hectares=4.0,
        soil_type="Black Cotton Soil",
        water_source="Borewell",
        active_crops=["Cotton", "Soybean"],
        farmer_category="Medium",
        gender="Male",
        caste_category="General",
        income_bracket="2-5 Lakh",
        has_bank_account=True,
        has_aadhaar=True,
        crop_season="Kharif",
        is_tenant=False,
        is_organic=False,
        recent_damage="Heavy Rain",
        metadata={"age": 48, "education": "12th pass", "family_size": 7, "damage_date": "2026-06-20"},
    ),
    Farmer(
        farmer_id="DEMO-F006",
        name="Harpreet Kaur",
        phone_number="+919876543215",
        state="Punjab",
        district="Amritsar",
        preferred_language="pa",
        land_size_hectares=1.5,
        soil_type="Alluvial",
        water_source="Canal",
        active_crops=["Rice", "Wheat"],
        farmer_category="Small",
        gender="Female",
        caste_category="SC",
        income_bracket="Below 1 Lakh",
        has_bank_account=True,
        has_aadhaar=True,
        crop_season="Kharif",
        is_tenant=False,
        is_organic=False,
        recent_damage=None,
        metadata={"age": 29, "education": "Graduate", "family_size": 4, "shg_member": True},
    ),
]


class DemoService:
    """
    Manages demo farmer profiles and simulation workflows.
    """

    def __init__(self) -> None:
        self._farmers: dict[str, Farmer] = {f.farmer_id: f for f in DEMO_FARMERS}

    def get_all_farmers(self) -> list[Farmer]:
        """Return all demo farmer profiles."""
        return list(self._farmers.values())

    def get_farmer(self, farmer_id: str) -> Farmer | None:
        """Get a specific demo farmer by ID."""
        return self._farmers.get(farmer_id)

    def get_farmer_by_phone(self, phone: str) -> Farmer | None:
        """Look up a demo farmer by phone number."""
        for farmer in self._farmers.values():
            if farmer.phone_number == phone:
                return farmer
        return None

    def get_farmer_summary(self, farmer: Farmer) -> dict[str, Any]:
        """Return a concise summary of a farmer profile for dashboard display."""
        return {
            "farmer_id": farmer.farmer_id,
            "name": farmer.name,
            "phone": farmer.phone_number,
            "state": farmer.state,
            "district": farmer.district,
            "category": farmer.farmer_category,
            "gender": farmer.gender,
            "land_hectares": farmer.land_size_hectares,
            "crops": farmer.active_crops,
            "language": farmer.preferred_language,
            "caste": farmer.caste_category,
            "recent_damage": farmer.recent_damage,
            "is_organic": farmer.is_organic,
            "is_tenant": farmer.is_tenant,
        }

    def generate_call_transcript(self, farmer: Farmer, schemes: list[dict[str, Any]]) -> list[dict[str, str]]:
        """
        Generate a realistic demo call transcript for a farmer.
        Used for simulated demo calls with live dashboard streaming.
        """
        name = farmer.name.split()[0]
        lang = farmer.preferred_language

        # Greeting phase
        transcript: list[dict[str, str]] = [
            {"role": "system", "text": f"📞 Incoming call from {farmer.phone_number} ({farmer.district}, {farmer.state})"},
            {"role": "assistant", "text": self._greeting(lang)},
        ]

        # Farmer speaks
        if lang == "hi":
            transcript.append({"role": "farmer", "text": f"हाँ, मेरा नाम {farmer.name} है। मुझे सरकारी योजनाओं के बारे में जानना है।"})
        elif lang == "pa":
            transcript.append({"role": "farmer", "text": f"ਹਾਂ ਜੀ, ਮੈਂ {farmer.name} ਹਾਂ। ਮੈਨੂੰ ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ ਬਾਰੇ ਜਾਣਨਾ ਹੈ।"})
        else:
            transcript.append({"role": "farmer", "text": f"Yes, I am {farmer.name}. I want to know about government schemes."})

        # Identity confirmation
        transcript.append({"role": "system", "text": f"🔍 Farmer identified: {farmer.name} ({farmer.farmer_id})"})
        transcript.append({"role": "system", "text": f"📋 Digital Twin loaded: {farmer.farmer_category} farmer, {farmer.land_size_hectares}ha, {', '.join(farmer.active_crops)}"})

        # Scheme matching
        transcript.append({"role": "system", "text": "🏛 Evaluating government schemes eligibility..."})

        # Scheme results
        eligible = [s for s in schemes if s.get("status") == "ELIGIBLE"]
        if eligible:
            scheme_names = ", ".join(s["title"] for s in eligible[:3])
            transcript.append({"role": "system", "text": f"✓ Found {len(eligible)} eligible scheme(s): {scheme_names}"})

            # AI response
            top = eligible[0]
            if lang == "hi":
                transcript.append({
                    "role": "assistant",
                    "text": (
                        f"{name} जी, आपकी प्रोफाइल के अनुसार, आप {top['title']} के लिए पात्र हैं। "
                        f"इसके तहत {top.get('benefits', '')} "
                        f"कृपया {', '.join(top.get('required_documents', [])[:3])} तैयार रखें। "
                        f"अधिक जानकारी के लिए {top.get('helpline', '')} पर कॉल करें।"
                    )
                })
            elif lang == "pa":
                transcript.append({
                    "role": "assistant",
                    "text": (
                        f"{name} ਜੀ, ਤੁਹਾਡੀ ਪ੍ਰੋਫਾਈਲ ਅਨੁਸਾਰ, ਤੁਸੀਂ {top['title']} ਲਈ ਯੋਗ ਹੋ। "
                        f"ਇਸ ਤਹਿਤ {top.get('benefits', '')} "
                        f"ਕਿਰਪਾ ਕਰਕੇ {', '.join(top.get('required_documents', [])[:3])} ਤਿਆਰ ਰੱਖੋ।"
                    )
                })
            else:
                transcript.append({
                    "role": "assistant",
                    "text": (
                        f"Based on your profile {name}, you are eligible for {top['title']}. "
                        f"{top.get('benefits', '')} "
                        f"Please keep {', '.join(top.get('required_documents', [])[:3])} ready. "
                        f"For more details, call {top.get('helpline', '')}."
                    )
                })
        else:
            transcript.append({"role": "system", "text": "⚠ No eligible schemes found for this profile."})
            transcript.append({"role": "assistant", "text": "We could not find matching schemes right now. Please provide more details."})

        # Closing
        if lang == "hi":
            transcript.append({"role": "assistant", "text": "किसान मित्र से संपर्क करने के लिए धन्यवाद। आपकी फसल लहलहाए!"})
        elif lang == "pa":
            transcript.append({"role": "assistant", "text": "ਕਿਸਾਨ ਮਿੱਤਰ ਨਾਲ ਸੰਪਰਕ ਕਰਨ ਲਈ ਧੰਨਵਾਦ। ਚੰਗੀ ਫਸਲ ਹੋਵੇ!"})
        else:
            transcript.append({"role": "assistant", "text": "Thank you for calling Kisan Mitra. Have a great harvest!"})

        transcript.append({"role": "system", "text": "📞 Call completed."})
        return transcript

    def _greeting(self, lang: str) -> str:
        greetings = {
            "hi": "नमस्ते, किसान मित्र एआई में आपका स्वागत है। मैं आपकी सरकारी योजनाओं से जुड़ी मदद करूंगा।",
            "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ, ਕਿਸਾਨ ਮਿੱਤਰ ਏਆਈ ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ। ਮੈਂ ਤੁਹਾਡੀ ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ ਵਿੱਚ ਮਦਦ ਕਰਾਂਗਾ।",
            "en": "Hello, welcome to Kisan Mitra AI. I will help you find government schemes you are eligible for.",
        }
        return greetings.get(lang, greetings["en"])
