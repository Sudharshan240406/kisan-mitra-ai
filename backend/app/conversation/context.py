import time
from typing import Any, Optional

from pydantic import BaseModel, Field


class ConversationContext(BaseModel):
    """
    State context representing conversation telemetry, memory, and session variables.
    """
    conversation_id: str = Field(..., description="Unique conversation session tracker.")
    session_id: str = Field(..., description="Active session token lookup.")
    farmer_id: Optional[str] = Field(default=None, description="Optional profile reference ID.")
    current_workflow: Optional[str] = Field(default=None, description="Workflow template ID active.")
    current_capability: Optional[str] = Field(default=None, description="Platform capability ID active.")
    current_state: str = Field(default="Greeting", description="Current conversation state machine state.")
    conversation_memory: list[dict[str, Any]] = Field(default_factory=list, description="Message exchange history logs.")
    reasoning_references: list[str] = Field(default_factory=list, description="Reasoning graph node pointers.")
    policy_references: list[str] = Field(default_factory=list, description="Applied policy check record pointers.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible JSON metadata parameters.")
    timeline: list[dict[str, Any]] = Field(default_factory=list, description="State transition history records.")


class ConversationContextManager:
    """
    Context manager supervising memory lifecycle of conversation context envelopes.
    """
    def __init__(self) -> None:
        self._contexts: dict[str, ConversationContext] = {}

    def get_or_create_context(self, conversation_id: str, session_id: str) -> ConversationContext:
        """
        Retrieves an active context by ID, or builds a new instance if missing.
        """
        if conversation_id not in self._contexts:
            new_ctx = ConversationContext(
                conversation_id=conversation_id,
                session_id=session_id,
                timeline=[{
                    "from_state": "None",
                    "to_state": "Greeting",
                    "timestamp": time.time(),
                    "reason": "Initialization"
                }]
            )
            self._contexts[conversation_id] = new_ctx
        return self._contexts[conversation_id]

    def save_context(self, context: ConversationContext) -> None:
        """
        Updates the registered context record.
        """
        self._contexts[context.conversation_id] = context

    def serialize_context(self, conversation_id: str) -> str:
        """
        Serializes context values to JSON representation.
        """
        ctx = self._contexts.get(conversation_id)
        if not ctx:
            raise KeyError(f"Context ID '{conversation_id}' not found.")
        return ctx.model_dump_json()
