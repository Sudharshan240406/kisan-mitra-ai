import logging
from enum import Enum
from typing import Any, Optional, cast

from app.telephony.sessions import CallSession

logger = logging.getLogger("kisan_mitra_ai.telephony.ivr")


class IVRState(str, Enum):
    """Supported states within the IVR call navigation system."""
    GREETING = "GREETING"
    LANGUAGE_SELECTION = "LANGUAGE_SELECTION"
    INTENT_CAPTURE = "INTENT_CAPTURE"
    CLARIFICATION = "CLARIFICATION"
    RECOMMENDATION_PLAYBACK = "RECOMMENDATION_PLAYBACK"
    CONFIRMATION = "CONFIRMATION"
    REPEAT_MENU = "REPEAT_MENU"
    EXIT = "EXIT"
    HUMAN_TRANSFER = "HUMAN_TRANSFER"


DEFAULT_IVR_CONFIG: dict[str, dict[str, Any]] = {
    "GREETING": {
        "prompts": {
            "hi": "नमस्ते, किसान मित्र एआई में आपका स्वागत है।",
            "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ, ਕਿਸਾਨ ਮਿੱਤਰ ਏਆਈ ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ।",
            "en": "Hello, welcome to Kisan Mitra AI."
        },
        "next": "LANGUAGE_SELECTION"
    },
    "LANGUAGE_SELECTION": {
        "prompts": {
            "hi": "भाषा चुनने के लिए: हिंदी के लिए 1 दबाएं, फॉर इंग्लिश प्रेस 2, ਪੰਜਾਬੀ ਲਈ 3 ਦਬਾਓ।",
            "pa": "भाषा चुनने के लिए: हिंदी के लिए 1 दबाएं, फॉर इंग्लिश प्रेस 2, ਪੰਜਾਬੀ ਲਈ 3 ਦਬਾਓ।",
            "en": "To select language: Press 1 for Hindi, 2 for English, 3 for Punjabi."
        },
        "dtmf": {
            "1": {"next": "INTENT_CAPTURE", "set_language": "hi"},
            "2": {"next": "INTENT_CAPTURE", "set_language": "en"},
            "3": {"next": "INTENT_CAPTURE", "set_language": "pa"}
        },
        "fallback": "LANGUAGE_SELECTION"
    },
    "INTENT_CAPTURE": {
        "prompts": {
            "hi": "मुख्य मेनू: मौसम की जानकारी के लिए 1 दबाएं, बाजार भाव के लिए 2 दबाएं, रोग नियंत्रण सलाह के लिए 3 दबाएं, या ग्राहक प्रतिनिधि से बात करने के लिए 9 दबाएं।",
            "pa": "ਮੁੱਖ ਮੇਨੂ: ਮੌਸਮ ਦੀ ਜਾਣਕਾਰੀ ਲਈ 1 ਦਬਾਓ, ਮੰਡੀ ਦੇ ਭਾਅ ਲਈ 2 ਦਬਾਓ, ਬਿਮਾਰੀ ਦੇ ਇਲਾਜ ਲਈ 3 ਦਬਾਓ, ਜਾਂ ਕਸਟਮਰ ਕੇਅਰ ਨਾਲ ਗੱਲ ਕਰਨ ਲਈ 9 ਦਬਾਓ।",
            "en": "Main menu: Press 1 for Weather, 2 for Market Prices, 3 for crop disease advice, or press 9 to speak with an agent."
        },
        "dtmf": {
            "1": {"next": "RECOMMENDATION_PLAYBACK", "query": "weather forecast"},
            "2": {"next": "RECOMMENDATION_PLAYBACK", "query": "market prices"},
            "3": {"next": "RECOMMENDATION_PLAYBACK", "query": "crop disease advice"},
            "9": {"next": "HUMAN_TRANSFER"}
        },
        "fallback": "INTENT_CAPTURE"
    },
    "CLARIFICATION": {
        "prompts": {
            "hi": "कृपया अधिक जानकारी प्रदान करें। अपनी समस्या रिकॉर्ड करने के लिए 1 दबाएं या मुख्य मेनू पर लौटने के लिए 9 दबाएं।",
            "pa": "ਕਿਰਪਾ ਕਰਕੇ ਹੋਰ ਜਾਣਕਾਰੀ ਦਿਓ। ਆਪਣੀ ਸਮੱਸਿਆ ਰਿਕਾਰਡ ਕਰਨ ਲਈ 1 ਦਬਾਓ ਜਾਂ ਮੁੱਖ ਮੇਨੂ ਤੇ ਜਾਣ ਲਈ 9 ਦਬਾਓ।",
            "en": "Please provide more details. Press 1 to record your query, or press 9 to return to the main menu."
        },
        "dtmf": {
            "1": {"next": "INTENT_CAPTURE", "voice_record": True},
            "9": {"next": "INTENT_CAPTURE"}
        },
        "fallback": "CLARIFICATION"
    },
    "RECOMMENDATION_PLAYBACK": {
        "prompts": {
            "hi": "यहाँ आपकी सलाह है: ",
            "pa": "ਇੱਥੇ ਤੁਹਾਡੀ ਸਲਾਹ ਹੈ: ",
            "en": "Here is your advisory recommendation: "
        },
        "next": "CONFIRMATION"
    },
    "CONFIRMATION": {
        "prompts": {
            "hi": "यदि आप सलाह समझ गए हैं तो 1 दबाएं। सलाह दोबारा सुनने के लिए 2 दबाएं। मुख्य मेनू पर लौटने के लिए 9 दबाएं।",
            "pa": "ਜੇਕਰ ਤੁਸੀਂ ਸਲਾਹ ਸਮਝ ਗਏ ਹੋ ਤਾਂ 1 ਦਬਾਓ। ਸਲਾਹ ਦੁਬਾਰਾ ਸੁਣਨ ਲਈ 2 ਦਬਾਓ। ਮੁੱਖ ਮੇਨੂ ਤੇ ਜਾਣ ਲਈ 9 ਦਬਾਓ।",
            "en": "If you understood the advisory, press 1. To repeat the advisory, press 2. To return to the main menu, press 9."
        },
        "dtmf": {
            "1": {"next": "EXIT"},
            "2": {"next": "RECOMMENDATION_PLAYBACK", "repeat": True},
            "9": {"next": "INTENT_CAPTURE"}
        },
        "fallback": "CONFIRMATION"
    },
    "HUMAN_TRANSFER": {
        "prompts": {
            "hi": "कृपया प्रतीक्षा करें, आपकी कॉल हमारे कृषि विशेषज्ञ को ट्रांसफर की जा रही है।",
            "pa": "ਕਿਰਪਾ ਕਰਕੇ ਇੰਤਜ਼ਾਰ ਕਰੋ, ਤੁਹਾਡੀ ਕਾਲ ਸਾਡੇ ਖੇਤੀਬਾੜੀ ਮਾਹਿਰ ਨੂੰ ਟ੍ਰਾਂਸਫਰ ਕੀਤੀ ਜਾ ਰਹੀ ਹੈ।",
            "en": "Please wait while we transfer your call to our agricultural specialist."
        },
        "next": "EXIT"
    },
    "EXIT": {
        "prompts": {
            "hi": "किसान मित्र से संपर्क करने के लिए धन्यवाद। आपका दिन शुभ हो!",
            "pa": "ਕਿਸਾਨ ਮਿੱਤਰ ਨਾਲ ਸੰਪਰਕ ਕਰਨ ਲਈ ਧੰਨਵਾਦ। ਤੁਹਾਡਾ ਦਿਨ ਵਧੀਆ ਰਹੇ!",
            "en": "Thank you for calling Kisan Mitra. Have a great day!"
        },
        "next": "CLOSED"
    }
}


class IVRStateMachine:
    """
    Configuration-driven IVR State Machine controlling menu trees, prompts,
    transitions, language updates, and DTMF routing fallback structures.
    """
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        self._config = config or DEFAULT_IVR_CONFIG

    async def get_prompt(self, state: str, language: str) -> str:
        """Retrieves the TTS string associated with the state and language."""
        state_cfg = self._config.get(state)
        if not state_cfg:
            return ""
        prompts = state_cfg.get("prompts", {})
        return cast(str, prompts.get(language, prompts.get("en", "")))

    async def transition(
        self,
        session: CallSession,
        trigger: str,
        input_val: Optional[str] = None
    ) -> tuple[IVRState, str]:
        """
        Manages direct transitions (e.g. from GREETING to LANGUAGE_SELECTION).
        Updates session state and returns the new IVR state and prompt text.
        """
        curr_state = session.current_ivr_state
        state_cfg = self._config.get(curr_state)

        if not state_cfg:
            session.current_ivr_state = IVRState.EXIT.value
            prompt = await self.get_prompt(IVRState.EXIT.value, session.language)
            return IVRState.EXIT, prompt

        next_state_str = state_cfg.get("next")
        if not next_state_str:
            # Check DTMF or fallback
            next_state_str = IVRState.EXIT.value

        session.current_ivr_state = next_state_str
        prompt = await self.get_prompt(next_state_str, session.language)
        return IVRState(next_state_str), prompt

    async def handle_dtmf(self, session: CallSession, digits: str) -> tuple[IVRState, str]:
        """
        Processes DTMF input digits, updates language or transitions,
        and returns the destination IVRState and corresponding prompt text.
        """
        curr_state = session.current_ivr_state
        state_cfg = self._config.get(curr_state)

        if not state_cfg or "dtmf" not in state_cfg:
            # State doesn't accept DTMF inputs
            prompt = await self.get_prompt(curr_state, session.language)
            return IVRState(curr_state), prompt

        dtmf_map = state_cfg["dtmf"]
        action = dtmf_map.get(digits)

        if not action:
            # Fallback
            fallback_state = state_cfg.get("fallback", curr_state)
            session.current_ivr_state = fallback_state
            prompt = "Invalid input. " + await self.get_prompt(fallback_state, session.language)
            return IVRState(fallback_state), prompt

        # Execute actions if configured
        next_state = action["next"]
        if "set_language" in action:
            session.language = action["set_language"]
            logger.info(f"Session '{session.call_id}' switched language to: {session.language}")

        if "query" in action:
            # Store intent query in metadata for CallManager to route
            session.metadata["intent_query"] = action["query"]

        session.current_ivr_state = next_state
        prompt = await self.get_prompt(next_state, session.language)
        return IVRState(next_state), prompt
