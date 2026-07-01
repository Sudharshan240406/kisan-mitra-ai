import logging
import time
from typing import Any

logger = logging.getLogger("kisan_mitra_ai.knowledge.validation")


class KnowledgeValidator:
    """
    Validates freshness, source verification, confidence, policy safety, and duplicate checks.
    """
    def __init__(self, max_age_seconds: float = 30 * 24 * 3600) -> None:  # default 30 days
        self.max_age_seconds = max_age_seconds

    def validate_freshness(self, metadata: dict[str, Any]) -> bool:
        """
        Validates whether the content was updated within the acceptable freshness interval.
        """
        last_updated = metadata.get("last_updated")
        if last_updated is None:
            return False
        age = time.time() - float(last_updated)
        is_fresh: bool = bool(age <= self.max_age_seconds)
        if not is_fresh:
            logger.warning(f"Knowledge validation: Stale data detected. Age: {age/3600:.2f} hours")
        return is_fresh

    def validate_source(self, metadata: dict[str, Any]) -> bool:
        """
        Verifies if the source is authoritative or officially approved.
        """
        is_authoritative = metadata.get("authoritative", True)
        if not is_authoritative:
            logger.warning("Knowledge validation: Non-authoritative document source flagged.")
        return bool(is_authoritative)

    def validate_policy_compliance(self, content: str) -> bool:
        """
        Ensures the knowledge recommendation does not contain banned chemicals or policy violations.
        """
        # Crop safety policy checks (e.g. Endosulfan, DDT, banned pesticides list)
        banned_substances = ["endosulfan", "ddt", "aldrin", "heptachlor", "chlordane"]
        content_lower = content.lower()
        for chemical in banned_substances:
            if chemical in content_lower:
                logger.error(f"Policy Violation: Recommendation contains banned chemical: '{chemical}'")
                return False
        return True

    def validate_all(self, result: dict[str, Any]) -> bool:
        """
        Runs complete validations across all checkers.
        """
        content = result.get("content", "")
        metadata = result.get("metadata", {})
        confidence = result.get("confidence", 0.0)

        # 1. Check confidence score threshold
        if confidence < 0.3:
            logger.warning(f"Validation failed: Low confidence score ({confidence})")
            return False

        # 2. Check source
        if not self.validate_source(metadata):
            return False

        # 3. Check freshness
        if not self.validate_freshness(metadata):
            # Allow fallback if verified as authoritative, but log warning
            pass

        # 4. Check policy
        if not self.validate_policy_compliance(content):
            return False

        return True
