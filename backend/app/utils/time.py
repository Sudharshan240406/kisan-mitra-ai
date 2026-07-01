import time
from datetime import UTC, datetime


def get_utc_now() -> datetime:
    """
    Get the current UTC time with timezone offset.
    """
    return datetime.now(UTC)

def get_timestamp_iso() -> str:
    """
    Get the current UTC timestamp formatted as ISO-8601 string.
    """
    return datetime.now(UTC).isoformat()

def get_current_epoch() -> float:
    """
    Get the current epoch time float.
    """
    return time.time()

def measure_latency_ms(start_epoch: float) -> float:
    """
    Calculate the elapsed time in milliseconds from a starting epoch.
    """
    return (time.time() - start_epoch) * 1000.0
