import logging
from typing import Any, Tuple

from app.ivr.call_session import CallSession
from app.ivr.ivr_flow import IVRFlow

logger = logging.getLogger("kisan_mitra_ai.ivr.dtmf_handler")


class DTMFHandler:
    """Processes DTMF input digits and routes user to the next state."""

    def __init__(self, ivr_flow: IVRFlow, language_selector: Any) -> None:
        self.ivr_flow = ivr_flow
        self.language_selector = language_selector

    async def handle_dtmf(self, session: CallSession, digits: str) -> Tuple[str, str]:
        current_state = session.current_ivr_state
        state_cfg = self.ivr_flow.config.get(current_state)

        if not state_cfg or "dtmf" not in state_cfg:
            # Current state does not support DTMF inputs
            prompt = self.ivr_flow.get_prompt(current_state, session.language)
            return current_state, prompt

        dtmf_map = state_cfg["dtmf"]
        action = dtmf_map.get(digits)

        # 1. Invalid Input Handling
        if not action:
            fallback_state = state_cfg.get("fallback", current_state)
            session.current_ivr_state = fallback_state
            prompt = "Invalid input. " + self.ivr_flow.get_prompt(fallback_state, session.language)
            return fallback_state, prompt

        # 2. Extract configuration actions
        next_state = action["next"]

        # 3. Action: Set Language (Language selection menu)
        if "set_language" in action:
            lang_code = action["set_language"]
            self.language_selector.select_language(session, lang_code)

        # 4. Action: Set Caller Type
        if "caller_type" in action:
            session.metadata["caller_type"] = action["caller_type"]
            logger.info(f"Session '{session.call_id}' caller type: {action['caller_type']}")

        # 5. Action: Query Intent
        if "query" in action:
            session.metadata["intent_query"] = action["query"]
            logger.info(f"Session '{session.call_id}' query registered: {action['query']}")

        # Update session state and return new prompt
        session.current_ivr_state = next_state
        prompt = self.ivr_flow.get_prompt(next_state, session.language)
        return next_state, prompt
