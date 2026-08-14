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

    def generate_call_transcript(
        self,
        farmer: Farmer,
        schemes: list[dict[str, Any]],
        question: str = "",
        voice_response: str = ""
    ) -> list[dict[str, str]]:
        """
        Generate a realistic demo call transcript for a farmer.
        Dynamic per question and preferred language.
        """
        name = farmer.name.split()[0]
        lang = farmer.preferred_language
        q_text = question.strip() if question else "What government schemes am I eligible for?"

        # Greeting phase
        transcript: list[dict[str, str]] = [
            {"role": "system", "text": f"📞 Incoming call from {farmer.phone_number} ({farmer.district}, {farmer.state})"},
            {"role": "assistant", "text": self._greeting(lang)},
        ]

        # Farmer speaks - dynamically translated per question & language
        farmer_speech = self._translate_question(q_text, lang, farmer.name)
        transcript.append({"role": "farmer", "text": farmer_speech})

        # Identity confirmation
        transcript.append({"role": "system", "text": f"🔍 Farmer identified: {farmer.name} ({farmer.farmer_id})"})
        transcript.append({"role": "system", "text": f"📋 Digital Twin loaded: {farmer.farmer_category} farmer, {farmer.land_size_hectares}ha, {', '.join(farmer.active_crops)}"})

        # Pipeline execution trace log
        q_low = q_text.lower()
        is_scheme_query = any(k in q_low for k in ["scheme", "government", "eligib", "yojana", "subsid"]) or not question

        if is_scheme_query:
            transcript.append({"role": "system", "text": "🏛 Evaluating government schemes eligibility..."})
            eligible = [s for s in schemes if s.get("status") == "ELIGIBLE"]
            if eligible:
                scheme_names = ", ".join(s["title"] for s in eligible[:3])
                transcript.append({"role": "system", "text": f"✓ Found {len(eligible)} eligible scheme(s): {scheme_names}"})
            else:
                transcript.append({"role": "system", "text": "⚠ No eligible schemes found for this profile."})
        else:
            transcript.append({"role": "system", "text": "🧠 Query routed through Multi-Agent Advisory Engine..."})
            transcript.append({"role": "system", "text": f"✓ Knowledge & Tiered LLM Reasoning completed for topic: '{q_text}'"})

        # AI Response
        spoken_output = voice_response or self.get_spoken_answer(q_text, "", lang, farmer.active_crops, farmer.district)
        transcript.append({"role": "assistant", "text": spoken_output})

        # Closing
        if lang == "hi":
            transcript.append({"role": "assistant", "text": "किसान मित्र से संपर्क करने के लिए धन्यवाद। आपकी फसल लहलहाए!"})
        elif lang == "pa":
            transcript.append({"role": "assistant", "text": "ਕਿਸਾਨ ਮਿੱਤਰ ਨਾਲ ਸੰਪਰਕ ਕਰਨ ਲਈ ਧੰਨਵਾਦ। ਚੰਗੀ ਫਸਲ ਹੋਵੇ!"})
        elif lang == "kn":
            transcript.append({"role": "assistant", "text": "ಕಿಸಾನ್ ಮಿತ್ರ ಅವರನ್ನು ಸಂಪರ್ಕಿಸಿದ್ದಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು. ನಿಮ್ಮ ಬೆಳೆ ಉತ್ತಮವಾಗಿರಲಿ!"})
        else:
            transcript.append({"role": "assistant", "text": "Thank you for calling Kisan Mitra. Have a great harvest!"})

        transcript.append({"role": "system", "text": "📞 Call completed."})
        return transcript

    def _greeting(self, lang: str) -> str:
        greetings = {
            "hi": "नमस्ते, किसान मित्र एआई में आपका स्वागत है। मैं आपकी सहायता कैसे कर सकता हूँ?",
            "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ, ਕਿਸਾਨ ਮਿੱਤਰ ਏਆਈ ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ। ਮੈਂ ਤੁਹਾਡੀ ਕੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
            "kn": "ನಮಸ್ಕಾರ, ಕಿಸಾನ್ ಮಿತ್ರ AI ಗೆ ಸ್ವಾಗತ. ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?",
            "en": "Hello, welcome to Kisan Mitra AI. How can I help you today?",
        }
        return greetings.get(lang, greetings["en"])

    def _translate_question(self, question: str, lang: str, farmer_name: str) -> str:
        name = farmer_name.split()[0]
        q_low = question.lower().strip()

        # Translations for standard demo queries across supported languages
        translations = {
            "hi": {
                "market_price": f"नमस्ते, मैं {farmer_name} बोल रहा हूँ। पंजाब में गेहूं का वर्तमान मंडी भाव क्या है?",
                "weather": f"नमस्ते, मैं {farmer_name} बोल रहा हूँ। लुधियाना में आज मौसम कैसा रहेगा?",
                "disease": f"नमस्ते, मैं {farmer_name}। मेरी गेहूं की फसल में पीले रतुआ के धब्बे हैं, मुझे क्या छिड़काव करना चाहिए?",
                "scheme": f"नमस्ते, मैं {farmer_name}। मैं किन सरकारी योजनाओं के लिए पात्र हूँ?",
                "irrigation": f"नमस्ते, मैं {farmer_name}। रबी सीजन में गेहूं की फसल को कितने पानी की आवश्यकता होती है?",
            },
            "kn": {
                "market_price": f"ನಮಸ್ಕಾರ, ನಾನು {farmer_name}. ಪಂಜಾಬ್‌ನಲ್ಲಿ ಗೋಧಿಯ ಪ್ರಸ್ತುತ ಮಂಡಿ ಬೆಲೆ ಎಷ್ಟು?",
                "weather": f"ನಮಸ್ಕಾರ, ನಾನು {farmer_name}. ಇಂದು ಲುಧಿಯಾನಾದಲ್ಲಿ ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ ಏನು?",
                "disease": f"ನಮಸ್ಕಾರ, ನಾನು {farmer_name}. ನನ್ನ ಗೋಧಿ ಬೆಳೆಯಲ್ಲಿ ಹಳದಿ ತುಕ್ಕು ಚುಕ್ಕೆಗಳಿವೆ, ನಾನು ಏನು ಸಿಂಪಡಿಸಬೇಕು?",
                "scheme": f"ನಮಸ್ಕಾರ, ನಾನು {farmer_name}. ನಾನು ಯಾವ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳಿಗೆ ಅರ್ಹನಾಗಿದ್ದೇನೆ?",
                "irrigation": f"ನಮಸ್ಕಾರ, ನಾನು {farmer_name}. ರಬಿ ಋತುವಿನಲ್ಲಿ ಗೋಧಿ ಬೆಳೆಗೆ ಎಷ್ಟು ನೀರು ಬೇಕು?",
            },
            "pa": {
                "market_price": f"ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ, ਮੈਂ {farmer_name} ਹਾਂ। ਪੰਜਾਬ ਵਿੱਚ ਕਣਕ ਦਾ ਮੌਜੂਦਾ ਮੰਡੀ ਭਾਅ ਕੀ ਹੈ?",
                "weather": f"ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ, ਮੈਂ {farmer_name} ਹਾਂ। ਅੱਜ ਲੁਧਿਆਣਾ ਵਿੱਚ ਮੌਸਮ ਕਿਹੋ ਜਿਹਾ ਰਹੇਗਾ?",
                "disease": f"ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ, ਮੈਂ {farmer_name}। ਮੇਰੀ ਕਣਕ ਦੀ ਫਸਲ ਵਿੱਚ ਪੀਲੇ ਕੁੰਗੀ ਦੇ ਧੱਬੇ ਹਨ, ਮੈਨੂੰ ਕੀ ਛਿੜਕਾਅ ਕਰਨਾ ਚਾਹੀਦਾ ਹੈ?",
                "scheme": f"ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ, ਮੈਂ {farmer_name}। ਮੈਂ ਕਿਹੜੀਆਂ ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ ਲਈ ਯੋਗ ਹਾਂ?",
                "irrigation": f"ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ, ਮੈਂ {farmer_name}। ਰਬੀ ਦੇ ਸੀਜ਼ਨ ਵਿੱਚ ਕਣਕ ਦੀ ਫਸਲ ਨੂੰ ਕਿੰਨੇ ਪਾਣੀ ਦੀ ਲੋੜ ਹੁੰਦੀ ਹੈ?",
            },
            "en": {
                "market_price": f"Hello, I am {farmer_name}. What is the current mandi rate for wheat in Punjab?",
                "weather": f"Hello, I am {farmer_name}. What is the weather forecast for Ludhiana today?",
                "disease": f"Hello, I am {farmer_name}. My wheat crop has yellow rust spots, what should I spray?",
                "scheme": f"Hello, I am {farmer_name}. What government schemes am I eligible for?",
                "irrigation": f"Hello, I am {farmer_name}. How much water does wheat crop need in Rabi season?",
            }
        }

        category = "scheme"
        if any(k in q_low for k in ["price", "mandi", "rate"]):
            category = "market_price"
        elif any(k in q_low for k in ["weather", "rain", "forecast"]):
            category = "weather"
        elif any(k in q_low for k in ["disease", "rust", "spot", "spray", "pest"]):
            category = "disease"
        elif any(k in q_low for k in ["water", "irrigation", "depth", "sow"]):
            category = "irrigation"
        elif any(k in q_low for k in ["scheme", "eligib", "yojana", "subsid"]):
            category = "scheme"

        lang_dict = translations.get(lang, translations["en"])
        return lang_dict.get(category, f"Hello, I am {farmer_name}. {question}")

    def get_spoken_answer(
        self,
        question: str,
        recommendation: str,
        lang: str,
        crops: list[str] = None,
        location: str = ""
    ) -> str:
        q_low = question.lower()
        crop_str = crops[0] if crops else "Wheat"
        loc_str = location or "Punjab"

        if any(k in q_low for k in ["price", "mandi", "rate"]):
            answers = {
                "hi": f"{loc_str} में {crop_str} का वर्तमान मंडी भाव ₹2,275 प्रति क्विंटल है। मंडी में कीमतें स्थिर बनी हुई हैं।",
                "kn": f"{loc_str} ದಲ್ಲಿ {crop_str} ನ ಪ್ರಸ್ತುತ ಮಂಡಿ ಬೆಲೆ ಕ್ವಿಂಟಾಲ್‌ಗೆ ₹2,275 ಆಗಿದೆ. ಬೆಲೆಗಳು ಸ್ಥಿರವಾಗಿವೆ.",
                "pa": f"{loc_str} ਵਿੱਚ {crop_str} ਦਾ ਮੌਜੂਦਾ ਮੰਡੀ ਭਾਅ ₹2,275 ਪ੍ਰਤੀ ਕੁਇੰਟਲ ਹੈ। ਕੀਮਤਾਂ ਸਥਿਰ ਹਨ।",
                "en": f"The current mandi rate for {crop_str} in {loc_str} is 2,275 INR per quintal. Prices are holding steady today."
            }
            return answers.get(lang, answers["en"])

        elif any(k in q_low for k in ["weather", "rain", "forecast"]):
            answers = {
                "hi": f"{loc_str} में मौसम साफ रहने की संभावना है। तापमान सामान्य रहेगा, खेत के कार्यों के लिए समय अनुकूल है।",
                "kn": f"{loc_str} ದಲ್ಲಿ ಹವಾಮಾನ ಮುನ್ಸೂಚನೆಯು ಸ್ಪಷ್ಟವಾಗಿರುತ್ತದೆ. ತಾಪಮಾನ ಸಾಮಾನ್ಯವಾಗಿರುತ್ತದೆ, ಕೃಷಿ ಕೆಲಸಕ್ಕೆ ಸೂಕ್ತವಾಗಿದೆ.",
                "pa": f"{loc_str} ਵਿੱਚ ਮੌਸਮ ਸਾਫ਼ ਰਹਿਣ ਦੀ ਸੰਭਾਵਨਾ ਹੈ। ਤਾਪਮਾਨ ਆਮ ਰਹੇਗਾ, ਖੇਤ ਦੇ ਕੰਮ ਲਈ ਸਮਾਂ ਅਨੁਕੂਲ ਹੈ।",
                "en": f"In {loc_str}, the weather forecast indicates clear skies with normal seasonal temperatures. Suitable for field work."
            }
            return answers.get(lang, answers["en"])

        elif any(k in q_low for k in ["disease", "rust", "spot", "spray"]):
            answers = {
                "hi": f"आपकी {crop_str} की फसल के लिए: पीले रतुआ नियंत्रण के लिए 0.1% प्रोपिकोनाज़ोल का छिड़काव करें और जल निकासी में सुधार करें।",
                "kn": f"ನಿಮ್ಮ {crop_str} ಬೆಳೆಗೆ: ಹಳದಿ ತುಕ್ಕು ನಿಯಂತ್ರಣಕ್ಕಾಗಿ 0.1% ಪ್ರೊಪಿಕೊನಜೋಲ್ ಸಿಂಪಡಿಸಿ ಮತ್ತು ಒಳಚರಂಡಿ ಸುಧಾರಿಸಿ.",
                "pa": f"ਤੁਹਾਡੀ {crop_str} ਦੀ ਫਸਲ ਲਈ: ਪੀਲੇ ਕੁੰਗੀ ਦੇ ਨਿਯੰਤਰਣ ਲਈ 0.1% ਪ੍ਰੋਪੀਕੋਨਾਜ਼ੋਲ ਦਾ ਛਿੜਕਾਅ ਕਰੋ।",
                "en": f"For {crop_str}: spray 0.1% Propiconazole to control yellow rust and ensure proper field drainage."
            }
            return answers.get(lang, answers["en"])

        elif any(k in q_low for k in ["water", "irrigation", "sow", "depth"]):
            answers = {
                "hi": f"रबी मौसम में {crop_str} की फसल को 4-5 सिंचाई (लगभग 400-450 mm पानी) की आवश्यकता होती है।",
                "kn": f"ರಬಿ ಋತುವಿನಲ್ಲಿ {crop_str} ಬೆಳೆಗೆ 4-5 ನೀರಾವರಿ (ಸುಮಾರು 400-450 ಮಿಮೀ ನೀರು) ಅಗತ್ಯವಿರುತ್ತದೆ.",
                "pa": f"ਰਬੀ ਦੇ ਸੀਜ਼ਨ ਵਿੱਚ {crop_str} ਦੀ ਫਸਲ ਨੂੰ 4-5 ਸਿੰਚਾਈਆਂ ਦੀ ਲੋੜ ਹੁੰਦੀ ਹੈ।",
                "en": f"For {crop_str} in Rabi season, 4-5 irrigations (approx 400-450 mm of water) are recommended at critical growth stages."
            }
            return answers.get(lang, answers["en"])

        elif any(k in q_low for k in ["scheme", "eligib", "yojana", "subsid"]):
            answers = {
                "hi": f"आप पीएम-किसान योजना के तहत 6,000 रुपये प्रति वर्ष 3 समान किस्तों में प्राप्त करने के लिए पात्र हैं।",
                "kn": f"ನೀವು ಪಿಎಂ-ಕಿಸಾನ್ ಯೋಜನೆಯಡಿಯಲ್ಲಿ ವರ್ಷಕ್ಕೆ 6,000 ರೂ.ಗಳನ್ನು ಪಡೆಯಲು ಅರ್ಹರಾಗಿದ್ದೀರಿ.",
                "pa": f"ਤੁਸੀਂ PM-Kisan ਯੋਜਨਾ ਦੇ ਤਹਿਤ ₹6,000 ਪ੍ਰਤੀ ਸਾਲ ਪ੍ਰਾਪਤ ਕਰਨ ਦੇ ਯੋਗ ਹੋ।",
                "en": f"Under the PM-Kisan scheme, eligible landholding farmer families receive 6,000 INR per year in 3 equal installments."
            }
            return answers.get(lang, answers["en"])

        if recommendation:
            return recommendation
        return f"Here is the advisory for {crop_str} in {loc_str}."
