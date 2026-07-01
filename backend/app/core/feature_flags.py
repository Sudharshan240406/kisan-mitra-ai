from app.core.config import Settings


class FeatureFlags:
    """
    Configuration-driven Feature Flag manager mapping system controls
    to environment settings.
    """
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        # Mapping flag keys to settings properties
        self._flag_map = {
            "reasoning.enabled": "FEATURE_REASONING_ENABLED",
            "workflow.enabled": "FEATURE_WORKFLOW_ENABLED",
            "policy.enabled": "FEATURE_POLICY_ENABLED",
            "telemetry.enabled": "FEATURE_TELEMETRY_ENABLED",
            "dashboard.enabled": "FEATURE_DASHBOARD_ENABLED",
            "voice.enabled": "FEATURE_VOICE_ENABLED",
            "sms.enabled": "FEATURE_SMS_ENABLED",
            "ivr.enabled": "FEATURE_IVR_ENABLED",
            "llm.enabled": "FEATURE_LLM_ENABLED",
            "debug.enabled": "FEATURE_DEBUG_ENABLED"
        }

    def is_enabled(self, flag_name: str) -> bool:
        """
        Determines if a feature flag is active under the current configuration.
        """
        property_name = self._flag_map.get(flag_name.strip().lower())
        if not property_name:
            return False
        return getattr(self._settings, property_name, False)
