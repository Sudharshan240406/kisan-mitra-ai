import uuid


def generate_uuid() -> str:
    """
    Generate a standard random UUIDv4 string.
    """
    return str(uuid.uuid4())

def generate_session_id(prefix: str = "KM-SES") -> str:
    """
    Generate a session ID string with a customizable prefix.
    """
    random_str = uuid.uuid4().hex[:12].upper()
    return f"{prefix}-{random_str}"

def generate_trace_id(prefix: str = "KM-TRC") -> str:
    """
    Generate a trace ID string for logging or execution graphs.
    """
    random_str = uuid.uuid4().hex[:16].upper()
    return f"{prefix}-{random_str}"
