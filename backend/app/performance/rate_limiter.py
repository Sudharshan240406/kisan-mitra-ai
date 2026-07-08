import logging
import time
from typing import Dict, Tuple

logger = logging.getLogger("kisan_mitra_ai.performance.rate_limiter")

class RateLimiter:
    """
    Token Bucket rate limiter ensuring fair use across client endpoints.
    """
    def __init__(self, capacity: int = 20, refill_rate: float = 5.0) -> None:
        self.capacity = capacity  # Maximum bucket capacity (supports burst handling)
        self.refill_rate = refill_rate  # Tokens refilled per second
        # key -> (tokens_count, last_refill_time)
        self._buckets: Dict[str, Tuple[float, float]] = {}

    def is_allowed(self, key: str) -> bool:
        """
        Deducts a single token from the bucket corresponding to the given key.
        Returns True if allowed, False if throttled.
        """
        now = time.time()
        if key not in self._buckets:
            # First request, initialize bucket at max capacity
            self._buckets[key] = (float(self.capacity), now)

        tokens, last_refill = self._buckets[key]

        # Calculate tokens refilled since last access
        elapsed = now - last_refill
        refilled = elapsed * self.refill_rate

        # Refill tokens, capped at max capacity
        new_tokens = min(float(self.capacity), tokens + refilled)

        if new_tokens >= 1.0:
            # Allow request, deduct 1 token
            self._buckets[key] = (new_tokens - 1.0, now)
            logger.debug(f"[RateLimiter] Request allowed for key '{key}'. Remaining tokens: {new_tokens - 1.0:.2f}")
            return True
        else:
            # Throttle request, keep count (but update last refill timestamp to prevent starving)
            self._buckets[key] = (new_tokens, now)
            logger.warning(f"[RateLimiter] Rate limit exceeded for key '{key}'. Throttled.")
            return False

    def clear(self) -> None:
        """
        Resets rate limits.
        """
        self._buckets.clear()
