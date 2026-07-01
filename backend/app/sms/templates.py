import logging
from typing import Any, Optional

logger = logging.getLogger("kisan_mitra_ai.sms.templates")

DEFAULT_TEMPLATES: dict[str, dict[str, str]] = {
    "en": {
        "gov_scheme": "Kisan Mitra: Hello {farmer_name}, new scheme '{scheme_name}' is available. Details: {details}.",
        "weather_alert": "Weather Alert: {region} weather is {weather_condition} ({temp}C). Please take precautions.",
        "market_price": "Market Rate: Crop {crop_name} is priced at Rs. {price}/qtl in market '{market}'.",
        "crop_advisory": "Crop Advisory: For {disease}, we recommend: {recommendation}.",
        "otp": "Your Kisan Mitra OTP verification code is {otp_code}. Valid for 10 minutes.",
        "appointment": "Reminder: Appointment with advisor '{advisor_name}' is set for {date} at {time}.",
        "general": "{advisory_text}"
    },
    "hi": {
        "gov_scheme": "किसान मित्र: नमस्ते {farmer_name}, नई सरकारी योजना '{scheme_name}' सक्रिय है। विवरण: {details}।",
        "weather_alert": "मौसम चेतावनी: {region} में मौसम {weather_condition} ({temp}C) रहेगा। कृपया सावधानी बरतें।",
        "market_price": "बाजार भाव: मंडी '{market}' में फसल {crop_name} का भाव रु {price}/क्विंटल है।",
        "crop_advisory": "फसल सलाह: {disease} के नियंत्रण हेतु सलाह: {recommendation}।",
        "otp": "आपका किसान मित्र ओटीपी कोड {otp_code} है। यह 10 मिनट के लिए मान्य है।",
        "appointment": "नियुक्ति अनुस्मारक: सलाहकार '{advisor_name}' के साथ {date} को {time} बजे आपकी नियुक्ति है।",
        "general": "{advisory_text}"
    },
    "kn": {
        "gov_scheme": "[KN] Scheme: {farmer_name}, scheme '{scheme_name}' details: {details}.",
        "weather_alert": "[KN] Weather Alert: {region} - {weather_condition} ({temp}C).",
        "market_price": "[KN] Market Update: {crop_name} price in '{market}' is Rs. {price}.",
        "crop_advisory": "[KN] Crop Advisory: For {disease} - {recommendation}.",
        "otp": "[KN] OTP: {otp_code}.",
        "appointment": "[KN] Appointment: {advisor_name} on {date} at {time}.",
        "general": "[KN] {advisory_text}"
    },
    "te": {
        "gov_scheme": "[TE] Scheme: {farmer_name}, scheme '{scheme_name}' details: {details}.",
        "weather_alert": "[TE] Weather Alert: {region} - {weather_condition} ({temp}C).",
        "market_price": "[TE] Market Update: {crop_name} price in '{market}' is Rs. {price}.",
        "crop_advisory": "[TE] Crop Advisory: For {disease} - {recommendation}.",
        "otp": "[TE] OTP: {otp_code}.",
        "appointment": "[TE] Appointment: {advisor_name} on {date} at {time}.",
        "general": "[TE] {advisory_text}"
    },
    "ta": {
        "gov_scheme": "[TA] Scheme: {farmer_name}, scheme '{scheme_name}' details: {details}.",
        "weather_alert": "[TA] Weather Alert: {region} - {weather_condition} ({temp}C).",
        "market_price": "[TA] Market Update: {crop_name} price in '{market}' is Rs. {price}.",
        "crop_advisory": "[TA] Crop Advisory: For {disease} - {recommendation}.",
        "otp": "[TA] OTP: {otp_code}.",
        "appointment": "[TA] Appointment: {advisor_name} on {date} at {time}.",
        "general": "[TA] {advisory_text}"
    }
}


class SMSTemplateEngine:
    """
    Agricultural configuration-driven template engine supporting multiple languages (EN, HI, KN, TE, TA).
    """
    def __init__(self, templates: Optional[dict[str, dict[str, str]]] = None) -> None:
        self._templates = templates or DEFAULT_TEMPLATES

    def render(self, template_key: str, language: str, **kwargs: Any) -> str:
        """
        Interpolates parameters into the language-specific template.
        """
        lang_dict = self._templates.get(language, self._templates.get("en", {}))
        template_str = lang_dict.get(template_key, lang_dict.get("general", "{advisory_text}"))

        # Safely interpolate to prevent KeyError on missing template keys
        try:
            # We clean up key values or parse missing placeholders
            clean_kwargs = {k: (v if v is not None else "") for k, v in kwargs.items()}
            # Fallback placeholders in case parameters are missing in kwargs
            import re
            placeholders = re.findall(r"\{([a-zA-Z0-9_]+)\}", template_str)
            for key in placeholders:
                if key not in clean_kwargs:
                    clean_kwargs[key] = f"[{key}]"

            rendered = template_str.format(**clean_kwargs)
            logger.info(f"Rendered SMS template '{template_key}' for language '{language}'.")
            return rendered
        except Exception as e:
            logger.error(f"Failed to render SMS template '{template_key}' for language '{language}': {e}")
            # Fallback to general advisory text if it exists
            return str(kwargs.get("advisory_text", template_str))
