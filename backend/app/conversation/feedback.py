from typing import Any, Optional

from pydantic import BaseModel, Field


class FeedbackRecord(BaseModel):
    """
    Agricultural feedback record tracking post-recommendation outcomes.
    """
    feedback_id: str = Field(..., description="Unique feedback record identifier.")
    conversation_id: str = Field(..., description="Target Conversation UUID reference.")
    decision_id: str = Field(..., description="Associated Decision ID reference.")
    action_taken: str = Field(..., description="Action taken ('Accepted', 'Ignored').")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Farmer conversation rating index (1-5).")
    farmer_notes: Optional[str] = Field(default=None, description="Free text notes provided by farmer.")
    outcome: Optional[str] = Field(default=None, description="Long-term crop/disease mitigation outcome description.")
    learning_signals: dict[str, Any] = Field(default_factory=dict, description="Extensible placeholders for ML learning data.")


class FeedbackEngine:
    """
    Feedback collection framework registering signals to evaluate advisory success.
    """
    def __init__(self) -> None:
        self._feedback_store: dict[str, FeedbackRecord] = {}

    def submit_feedback(self, feedback: FeedbackRecord) -> None:
        """
        Registers farmer feedback.
        """
        self._feedback_store[feedback.feedback_id] = feedback

    def get_feedback_by_conversation(self, conversation_id: str) -> list[FeedbackRecord]:
        """
        Retrieves all registered feedback records matching a conversation.
        """
        return [r for r in self._feedback_store.values() if r.conversation_id == conversation_id]
