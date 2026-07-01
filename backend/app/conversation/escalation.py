import time
from typing import Any, Optional

from pydantic import BaseModel, Field


class EscalationRecord(BaseModel):
    """
    Escalation profile representing details of external human expert referrals.
    """
    escalation_id: str = Field(..., description="Unique referral lookup tracker.")
    conversation_id: str = Field(..., description="Target Conversation ID trace reference.")
    escalation_criteria: str = Field(..., description="Rule category triggering reference.")
    priority: str = Field(..., description="Urgency categorization ('High', 'Medium', 'Low').")
    reason: str = Field(..., description="Diagnostic context notes explaining referral.")
    suggested_specialist: str = Field(..., description="Specialist department lookup identifier.")
    escalation_state: str = Field(default="Initiated", description="Escalation status ('Initiated', 'Resolved').")
    timestamp: float = Field(default_factory=time.time, description="Creation epoch timestamp.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata placeholder properties.")


class HumanEscalationManager:
    """
    Human Escalation Manager supervising ticket workflows for manual review handovers.
    """
    def __init__(self) -> None:
        self._escalations: dict[str, EscalationRecord] = {}

    def trigger_escalation(
        self,
        conversation_id: str,
        criteria: str,
        reason: str,
        priority: str = "Medium"
    ) -> EscalationRecord:
        """
        Registers a new manual handover referral ticket.
        """
        import uuid
        escalation_id = f"ESC-{str(uuid.uuid4())[:8]}"

        # Resolve suggested specialist mapping
        crit_key = criteria.strip().lower()
        if "disease" in crit_key or "pest" in crit_key:
            specialist = "Agricultural Expert"
        elif "subsidy" in crit_key or "scheme" in crit_key:
            specialist = "Government Officer"
        elif "animal" in crit_key or "livestock" in crit_key or "veterinary" in crit_key:
            specialist = "Veterinarian"
        elif "complaint" in crit_key or "call" in crit_key:
            specialist = "Call Center"
        else:
            specialist = "District Officer"

        record = EscalationRecord(
            escalation_id=escalation_id,
            conversation_id=conversation_id,
            escalation_criteria=criteria,
            priority=priority,
            reason=reason,
            suggested_specialist=specialist
        )

        self._escalations[escalation_id] = record
        return record

    def get_escalation(self, escalation_id: str) -> Optional[EscalationRecord]:
        """
        Retrieves a referral record by ID.
        """
        return self._escalations.get(escalation_id)

    def resolve_escalation(self, escalation_id: str, status: str = "Resolved") -> None:
        """
        Updates referral record status to resolved.
        """
        record = self._escalations.get(escalation_id)
        if not record:
            raise KeyError(f"Escalation ticket '{escalation_id}' not found.")
        record.escalation_state = status
