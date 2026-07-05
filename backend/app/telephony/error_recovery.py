"""
Kisan Mitra AI — Telephony Error Recovery
============================================
Graceful error handling for IVR call scenarios:
  - No speech detected
  - Poor audio quality
  - Unknown caller
  - Network delay
  - No schemes found
  - Missing farmer information
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("kisan_mitra_ai.telephony.error_recovery")


class ErrorRecovery:
    """
    Provides graceful recovery prompts for various IVR failure modes.
    All prompts are available in Hindi, Punjabi, and English.
    """

    RECOVERY_PROMPTS: dict[str, dict[str, str]] = {
        "no_speech": {
            "hi": "मुझे आपकी आवाज़ सुनाई नहीं दी। कृपया दोबारा बोलें या मेनू से विकल्प चुनने के लिए नंबर दबाएं।",
            "pa": "ਮੈਨੂੰ ਤੁਹਾਡੀ ਆਵਾਜ਼ ਸੁਣਾਈ ਨਹੀਂ ਦਿੱਤੀ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਬੋਲੋ ਜਾਂ ਮੇਨੂ ਤੋਂ ਨੰਬਰ ਦਬਾਓ।",
            "en": "I could not hear you. Please speak again or press a number to select from the menu.",
        },
        "poor_audio": {
            "hi": "आवाज़ की गुणवत्ता ठीक नहीं है। कृपया शांत जगह से दोबारा कॉल करें या धीरे-धीरे बोलें।",
            "pa": "ਆਵਾਜ਼ ਦੀ ਕੁਆਲਿਟੀ ਠੀਕ ਨਹੀਂ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਸ਼ਾਂਤ ਜਗ੍ਹਾ ਤੋਂ ਦੁਬਾਰਾ ਕਾਲ ਕਰੋ।",
            "en": "The audio quality is poor. Please try calling from a quieter place or speak slowly.",
        },
        "unknown_caller": {
            "hi": "आपका नंबर हमारे रिकॉर्ड में नहीं है। क्या आप नए किसान के रूप में रजिस्टर करना चाहेंगे? 1 दबाएं हाँ, 2 दबाएं गेस्ट के रूप में जारी रखें।",
            "pa": "ਤੁਹਾਡਾ ਨੰਬਰ ਸਾਡੇ ਰਿਕਾਰਡ ਵਿੱਚ ਨਹੀਂ ਹੈ। ਕੀ ਤੁਸੀਂ ਨਵੇਂ ਕਿਸਾਨ ਵਜੋਂ ਰਜਿਸਟਰ ਕਰਨਾ ਚਾਹੋਗੇ? 1 ਦਬਾਓ ਹਾਂ, 2 ਦਬਾਓ ਗੈਸਟ ਵਜੋਂ।",
            "en": "Your number is not in our records. Would you like to register as a new farmer? Press 1 for yes, 2 to continue as guest.",
        },
        "network_delay": {
            "hi": "कृपया प्रतीक्षा करें, हम आपकी जानकारी ला रहे हैं। इसमें कुछ सेकंड लग सकते हैं।",
            "pa": "ਕਿਰਪਾ ਕਰਕੇ ਇੰਤਜ਼ਾਰ ਕਰੋ, ਅਸੀਂ ਤੁਹਾਡੀ ਜਾਣਕਾਰੀ ਲੱਭ ਰਹੇ ਹਾਂ।",
            "en": "Please wait while we fetch your information. This may take a few seconds.",
        },
        "no_schemes": {
            "hi": "वर्तमान में आपकी प्रोफ़ाइल से मिलती-जुलती कोई योजना नहीं मिली। कृपया अपने ज़िले के कृषि कार्यालय से संपर्क करें या 1800-180-1551 पर कॉल करें।",
            "pa": "ਵਰਤਮਾਨ ਵਿੱਚ ਤੁਹਾਡੀ ਪ੍ਰੋਫਾਈਲ ਨਾਲ ਮੇਲ ਖਾਂਦੀ ਕੋਈ ਯੋਜਨਾ ਨਹੀਂ ਮਿਲੀ। ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ ਜ਼ਿਲ੍ਹੇ ਦੇ ਖੇਤੀ ਦਫ਼ਤਰ ਨਾਲ ਸੰਪਰਕ ਕਰੋ।",
            "en": "No matching schemes were found for your profile currently. Please contact your district agriculture office or call 1800-180-1551.",
        },
        "missing_info": {
            "hi": "आपकी पात्रता जाँचने के लिए कुछ और जानकारी चाहिए। कृपया अपनी जमीन का आकार और फसल बताएं।",
            "pa": "ਤੁਹਾਡੀ ਯੋਗਤਾ ਜਾਂਚਣ ਲਈ ਕੁਝ ਹੋਰ ਜਾਣਕਾਰੀ ਚਾਹੀਦੀ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੀ ਜ਼ਮੀਨ ਦਾ ਆਕਾਰ ਅਤੇ ਫ਼ਸਲ ਦੱਸੋ।",
            "en": "We need more information to check your eligibility. Please tell us your land size and the crops you grow.",
        },
        "system_error": {
            "hi": "हमें तकनीकी समस्या आ रही है। कृपया कुछ देर बाद दोबारा कॉल करें। असुविधा के लिए क्षमा करें।",
            "pa": "ਸਾਨੂੰ ਤਕਨੀਕੀ ਸਮੱਸਿਆ ਆ ਰਹੀ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਕੁਝ ਦੇਰ ਬਾਅਦ ਦੁਬਾਰਾ ਕਾਲ ਕਰੋ।",
            "en": "We are experiencing a technical issue. Please try calling back in a few minutes. We apologize for the inconvenience.",
        },
        "timeout_warning": {
            "hi": "क्या आप अभी भी लाइन पर हैं? कृपया कोई भी बटन दबाएं या बोलें।",
            "pa": "ਕੀ ਤੁਸੀਂ ਅਜੇ ਵੀ ਲਾਈਨ ਤੇ ਹੋ? ਕਿਰਪਾ ਕਰਕੇ ਕੋਈ ਵੀ ਬਟਨ ਦਬਾਓ ਜਾਂ ਬੋਲੋ।",
            "en": "Are you still there? Please press any button or speak.",
        },
    }

    MAX_RETRIES = 3

    def get_recovery_prompt(self, error_type: str, language: str = "hi") -> str:
        """Get a localized recovery prompt for a given error type."""
        prompts = self.RECOVERY_PROMPTS.get(error_type, self.RECOVERY_PROMPTS["system_error"])
        return prompts.get(language, prompts.get("en", ""))

    def should_retry(self, retry_count: int) -> bool:
        """Check if we should retry or escalate."""
        return retry_count < self.MAX_RETRIES

    def get_escalation_prompt(self, language: str = "hi") -> str:
        """Get the human transfer prompt after max retries."""
        prompts = {
            "hi": "हम आपकी कॉल हमारे कृषि विशेषज्ञ को ट्रांसफर कर रहे हैं। कृपया प्रतीक्षा करें।",
            "pa": "ਅਸੀਂ ਤੁਹਾਡੀ ਕਾਲ ਸਾਡੇ ਖੇਤੀ ਮਾਹਿਰ ਨੂੰ ਟ੍ਰਾਂਸਫਰ ਕਰ ਰਹੇ ਹਾਂ। ਕਿਰਪਾ ਕਰਕੇ ਇੰਤਜ਼ਾਰ ਕਰੋ।",
            "en": "We are transferring your call to our agricultural specialist. Please hold.",
        }
        return prompts.get(language, prompts["en"])

    def classify_error(self, error_context: dict[str, Any]) -> str:
        """Classify an error into a recovery category."""
        if error_context.get("no_speech"):
            return "no_speech"
        if "low_confidence" in error_context and error_context["low_confidence"] < 0.3:
            return "poor_audio"
        if error_context.get("unknown_caller"):
            return "unknown_caller"
        if error_context.get("timeout"):
            return "network_delay"
        if error_context.get("no_schemes"):
            return "no_schemes"
        if error_context.get("missing_fields"):
            return "missing_info"
        return "system_error"
