import logging
from typing import Any, Optional

logger = logging.getLogger("kisan_mitra_ai.ivr.language_selector")


class LanguageSelector:
    """Manages language selection and updates the farmer's Digital Twin settings."""
    def __init__(self, container: Any) -> None:
        self.container = container
        # Mapping DTMF digits to language codes
        self.dtmf_language_map = {
            "1": "hi",  # Hindi
            "2": "en",  # English
            "3": "kn",  # Kannada
            "4": "te",  # Telugu
            "5": "ta",  # Tamil
            "6": "pa",  # Punjabi (backward compatibility)
        }

    @property
    def twin_manager(self) -> Optional[Any]:
        return getattr(self.container, "twin_manager", None)

    def get_language_from_dtmf(self, digits: str) -> Optional[str]:
        return self.dtmf_language_map.get(digits)

    def select_language(self, session: Any, language_code: str) -> None:
        session.language = language_code
        logger.info(f"Session '{session.call_id}' language set to '{language_code}'")
        
        # If a farmer profile exists, persist the preferred language in the Digital Twin
        farmer_id = session.farmer_id or session.metadata.get("farmer_id")
        if farmer_id:
            try:
                twin = self.twin_manager.get_twin(farmer_id)
                if twin and twin.profile:
                    twin.profile.preferred_language = language_code
                    self.twin_manager.update_twin(twin)
                    logger.info(f"Updated preferred_language to '{language_code}' in Digital Twin for farmer '{farmer_id}'")
            except Exception as e:
                logger.error(f"Failed to update preferred language in Digital Twin: {e}")
