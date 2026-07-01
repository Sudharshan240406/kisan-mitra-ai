from typing import Any


class KisanMitraException(Exception):
    """
    Base exception for all Kisan Mitra AI application errors.
    """
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class AgentException(KisanMitraException):
    """
    Raised when an error occurs during agent execution, validation, or lifecycle.
    """
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, status_code=422, details=details)

class ConfigurationException(KisanMitraException):
    """
    Raised when there is a missing, invalid, or conflicting configuration parameter.
    """
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, status_code=500, details=details)

class ValidationException(KisanMitraException):
    """
    Raised when inputs or outputs fail schema validation or semantic logic verification.
    """
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, status_code=400, details=details)

class ProviderException(KisanMitraException):
    """
    Raised when LLM providers or external services fail to respond or return error responses.
    """
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, status_code=502, details=details)

class OrchestratorException(KisanMitraException):
    """
    Raised when the orchestrator encounters errors coordinating the multi-agent graph.
    """
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, status_code=500, details=details)
