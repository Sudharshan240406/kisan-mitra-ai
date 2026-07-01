import json
import logging
import logging.handlers
import os
import sys
from contextvars import ContextVar
from datetime import datetime

from app.core.config import settings

# Thread-local / ContextVar tracking variables for request telemetry correlation
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
session_id_var: ContextVar[str] = ContextVar("session_id", default="")

class ContextPropagatingFilter(logging.Filter):
    """
    Filter that injects context-propagated variables into the log record context.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = trace_id_var.get() or "N/A"
        record.request_id = request_id_var.get() or "N/A"
        record.session_id = session_id_var.get() or "N/A"
        return True

class JSONFormatter(logging.Formatter):
    """
    Structured JSON log formatter for production logging.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "filename": record.filename,
            "lineno": record.lineno,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", "N/A"),
            "request_id": getattr(record, "request_id", "N/A"),
            "session_id": getattr(record, "session_id", "N/A")
        }

        # Capture stack traces if an exception occurred
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Capture extra fields passed to logger
        if hasattr(record, "extra_fields"):
            log_data["extra_fields"] = record.extra_fields

        return json.dumps(log_data)

def setup_logging() -> logging.Logger:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    log_dir = settings.LOG_DIR

    # Guarantee log directory exists
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        # Fallback to local app logs folder if permission denied in root dir
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)

    # Establish the standard formatter
    formatter: logging.Formatter
    if settings.LOG_FORMAT.lower() == "json":
        formatter = JSONFormatter()
    else:
        log_format = (
            "[%(asctime)s] %(levelname)-8s in %(module)s "
            "[Trace: %(trace_id)s, Request: %(request_id)s, Session: %(session_id)s]: %(message)s"
        )
        formatter = logging.Formatter(log_format)

    # Context filter to propagate request/session correlations
    context_filter = ContextPropagatingFilter()

    # 1. Console Stream Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.addFilter(context_filter)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Configure root logger
    root_logger = logging.getLogger()

    # Clean default handlers to prevent duplication
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    root_logger.addHandler(console_handler)
    root_logger.setLevel(log_level)

    # Configure file rotating handlers in production / production logging profile
    try:
        # 2. General Application Log Handler (all levels)
        app_file = os.path.join(log_dir, "app.log")
        app_handler = logging.handlers.RotatingFileHandler(
            app_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        app_handler.addFilter(context_filter)
        app_handler.setFormatter(formatter)
        app_handler.setLevel(log_level)
        root_logger.addHandler(app_handler)

        # 3. Error and Warning Log Handler (levels >= WARNING)
        error_file = os.path.join(log_dir, "error.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        error_handler.addFilter(context_filter)
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.WARNING)
        root_logger.addHandler(error_handler)

        # 4. Security Logs Router (Auth, policy violations, compliance events)
        security_file = os.path.join(log_dir, "security.log")
        security_handler = logging.handlers.RotatingFileHandler(
            security_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        security_handler.addFilter(context_filter)
        security_handler.setFormatter(formatter)
        security_handler.setLevel(logging.INFO)

        security_logger = logging.getLogger("kisan_mitra_ai.security")
        security_logger.addHandler(security_handler)
        security_logger.propagate = True

        # 5. Governance Audit Ledger Logs Router
        audit_file = os.path.join(log_dir, "audit.log")
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        audit_handler.addFilter(context_filter)
        audit_handler.setFormatter(formatter)
        audit_handler.setLevel(logging.INFO)

        audit_logger = logging.getLogger("kisan_mitra_ai.audit")
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = True

    except Exception as e:
        # Log to stderr if we fail to bind log files (e.g. read-only filesystem)
        sys.stderr.write(f"WARNING: Could not initialize rotating log files: {e}\n")

    # Align uvicorn web servers to log levels
    logging.getLogger("uvicorn.error").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(log_level)

    logger = logging.getLogger("kisan_mitra_ai")
    logger.info("Structured logging platform initialized successfully.", extra={"extra_fields": {"log_dir": log_dir, "format": settings.LOG_FORMAT}})
    return logger
