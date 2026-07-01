import time
from typing import Any, Optional

from pydantic import BaseModel, Field


class DecisionAuditRecord(BaseModel):
    """
    Structured record representing a single advisory decision trace entry.
    """
    decision_id: str = Field(..., description="Target Decision UUID reference.")
    conversation_id: str = Field(..., description="Active Conversation ID reference.")
    workflow_version: str = Field(..., description="Running version of the execution workflow.")
    capability: str = Field(..., description="Active capability invoked.")
    decision_strategy: str = Field(..., description="Consensus resolution strategy type name.")
    policy_version: str = Field(..., description="Governing policy engine semantic version.")
    evidence_ids: list[str] = Field(..., description="Evidence records mapped to this decision.")
    reasoning_graph_id: str = Field(..., description="Tracing graph ID pointer.")
    confidence: float = Field(..., description="Resolved consensus confidence value.")
    safety_assessment: dict[str, Any] = Field(..., description="Consolidated safety metrics outcome.")
    timestamp: float = Field(default_factory=time.time, description="Creation epoch timestamp.")
    future_prompt_version: str = Field(default="1.0.0", description="Future prompt registry version tag.")
    future_outcome: Optional[str] = Field(default=None, description="Long-term agronomic outcome feedback.")
    audit_status: str = Field(default="Pending", description="Verification auditing status.")


class DecisionAuditTrail:
    """
    Decision Audit Trail (DAT) ledger managing advisory traces historical data.
    """
    def __init__(self) -> None:
        self._records: dict[str, DecisionAuditRecord] = {}

    def log_record(self, record: DecisionAuditRecord) -> None:
        """
        Appends a new audit record to the tracking trail.
        """
        self._records[record.decision_id] = record

    def get_record(self, decision_id: str) -> Optional[DecisionAuditRecord]:
        """
        Looks up a registered record by ID.
        """
        return self._records.get(decision_id)

    def get_records(self, conversation_id: Optional[str] = None) -> list[DecisionAuditRecord]:
        """
        Returns records, optionally matching a specific conversation.
        """
        all_records = list(self._records.values())
        if conversation_id:
            return [r for r in all_records if r.conversation_id == conversation_id]
        return all_records

    def update_outcome(self, decision_id: str, outcome: str, status: str = "Audited") -> None:
        """
        Updates long-term outcome feedback details.
        """
        record = self._records.get(decision_id)
        if not record:
            raise KeyError(f"Audit record '{decision_id}' not found.")
        record.future_outcome = outcome
        record.audit_status = status
