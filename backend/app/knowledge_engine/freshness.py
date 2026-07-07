import logging
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("kisan_mitra_ai.knowledge_engine.freshness")

class FreshnessScorer:
    """
    Computes a freshness score for document metadata, taking into account
    last_updated age decay, deprecation status, validity period, and semantic versions.
    """
    def __init__(self, decay_period_days: float = 365.0) -> None:
        self.decay_period_days = decay_period_days

    def parse_version(self, version_str: str) -> Tuple[int, ...]:
        """
        Parses a semantic version string (e.g. '2.1.0') into an integer tuple for comparison.
        """
        if not version_str:
            return (1, 0, 0)
        try:
            # Strip non-numeric and split by dot
            cleaned = "".join(c for c in version_str if c.isdigit() or c == ".").strip(".")
            return tuple(map(int, cleaned.split(".")))
        except Exception:
            logger.warning(f"Failed to parse version string '{version_str}', using fallback (1, 0, 0)")
            return (1, 0, 0)

    def is_valid(self, metadata: Dict[str, Any], current_time: Optional[float] = None) -> bool:
        """
        Checks if the document is currently valid based on validity period and deprecation date.
        """
        now = current_time or time.time()

        # Check deprecation date
        dep_date = metadata.get("deprecation_date")
        if dep_date is not None and now >= dep_date:
            return False

        # Check validity period
        valid_period = metadata.get("validity_period")
        if isinstance(valid_period, dict):
            start = valid_period.get("start")
            end = valid_period.get("end")
            if start is not None and now < start:
                return False
            if end is not None and now > end:
                return False

        return True

    def calculate_freshness_score(self, metadata: Dict[str, Any], current_time: Optional[float] = None) -> float:
        """
        Calculates a freshness score between 0.0 and 1.0.
        Invalid or deprecated documents return 0.0.
        """
        now = current_time or time.time()

        if not self.is_valid(metadata, now):
            return 0.0

        # Calculate time decay
        last_updated = metadata.get("last_updated")
        if last_updated is None:
            # If not specified, default to 0.5 freshness
            return 0.5

        # Calculate age in days
        age_seconds = max(0.0, now - last_updated)
        age_days = age_seconds / (24 * 3600)

        # Decay formula: linear decay from 1.0 down to 0.1 over decay_period_days, then plateaus at 0.1
        decay = 1.0 - (age_days / self.decay_period_days)
        freshness = max(0.1, decay)

        # Apply a minor boost for newer semantic versions (e.g. up to +0.05)
        version_str = metadata.get("version", "1.0.0")
        v_tuple = self.parse_version(version_str)
        # Scale version number (major * 0.02 + minor * 0.005) capped at 0.05
        version_boost = min(0.05, (v_tuple[0] * 0.02) + (v_tuple[1] * 0.005 if len(v_tuple) > 1 else 0.0))

        final_score = min(1.0, freshness + version_boost)
        return float(round(final_score, 4))
