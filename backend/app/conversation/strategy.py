from enum import Enum


class InteractionStrategy(str, Enum):
    """
    Taxonomy of agricultural dialog strategies.
    """
    DIRECT_RECOMMENDATION = "Direct Recommendation"
    RECOMMENDATION_WITH_CAUTION = "Recommendation with Caution"
    CLARIFICATION_REQUIRED = "Clarification Required"
    EDUCATIONAL_GUIDANCE = "Educational Guidance"
    EMERGENCY_PLACEHOLDER = "Emergency Placeholder"
    ESCALATION_PLACEHOLDER = "Escalation Placeholder"
    LOW_CONFIDENCE_RESPONSE = "Low Confidence Response"
    MISSING_INFORMATION_RESPONSE = "Missing Information Response"


class ResponseStrategy(str, Enum):
    """
    Representational response formatting models.
    """
    SHORT_RESPONSE = "Short Response"
    DETAILED_RESPONSE = "Detailed Response"
    EDUCATIONAL_RESPONSE = "Educational Response"
    STEP_BY_STEP_GUIDANCE = "Step-by-Step Guidance"
    EMERGENCY_PLACEHOLDER = "Emergency Placeholder"
    FUTURE_VOICE_MODE = "Future Voice Mode"
    FUTURE_SMS_MODE = "Future SMS Mode"
    FUTURE_MOBILE_MODE = "Future Mobile Mode"
    FUTURE_WHATSAPP_MODE = "Future WhatsApp Mode"


class InteractionStrategyEngine:
    """
    Interaction selector applying priority filters based on trust score indicators.
    """
    def select_strategy(
        self,
        confidence: float,
        risk: float,
        policy_passed: bool,
        missing_fields: list[str],
        evidence_quality: float,
        reasoning_quality: float
    ) -> InteractionStrategy:
        """
        Determines the conversation interaction strategy.
        """
        if risk > 0.8:
            return InteractionStrategy.ESCALATION_PLACEHOLDER

        if risk > 0.5 or not policy_passed:
            return InteractionStrategy.RECOMMENDATION_WITH_CAUTION

        if missing_fields:
            return InteractionStrategy.MISSING_INFORMATION_RESPONSE

        if confidence < 0.5 or evidence_quality < 0.6:
            return InteractionStrategy.LOW_CONFIDENCE_RESPONSE

        if reasoning_quality > 0.8:
            return InteractionStrategy.EDUCATIONAL_GUIDANCE

        return InteractionStrategy.DIRECT_RECOMMENDATION


class ResponseStrategyEngine:
    """
    Response format adapter resolving presentation styles.
    """
    def resolve_response_format(
        self,
        interaction_strategy: InteractionStrategy,
        preferred_channel: str = "text"
    ) -> ResponseStrategy:
        """
        Maps conversational contexts to appropriate response strategies.
        """
        chan = preferred_channel.strip().lower()
        channel_map = {
            "voice": ResponseStrategy.FUTURE_VOICE_MODE,
            "sms": ResponseStrategy.FUTURE_SMS_MODE,
            "whatsapp": ResponseStrategy.FUTURE_WHATSAPP_MODE,
            "mobile": ResponseStrategy.FUTURE_MOBILE_MODE,
        }
        if chan in channel_map:
            return channel_map[chan]

        strategy_map = {
            InteractionStrategy.ESCALATION_PLACEHOLDER: ResponseStrategy.EMERGENCY_PLACEHOLDER,
            InteractionStrategy.EDUCATIONAL_GUIDANCE: ResponseStrategy.EDUCATIONAL_RESPONSE,
            InteractionStrategy.MISSING_INFORMATION_RESPONSE: ResponseStrategy.STEP_BY_STEP_GUIDANCE,
        }
        return strategy_map.get(interaction_strategy, ResponseStrategy.SHORT_RESPONSE)
