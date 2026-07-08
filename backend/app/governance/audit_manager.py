import logging
import os
import time
from typing import List, Optional

from pydantic import BaseModel, Field

from .compliance_engine import ComplianceRecord
from .explainability_engine import Explanation
from .policy_engine import PolicyViolation
from .rule_engine import RuleResult

logger = logging.getLogger("kisan_mitra_ai.governance.audit")

class AuditRecord(BaseModel):
    execution_id: str
    tenant_id: Optional[str] = None
    organization_id: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)
    user_id: str
    query: str
    response_text: str
    policy_violations: List[PolicyViolation] = Field(default_factory=list)
    rule_results: List[RuleResult] = Field(default_factory=list)
    compliance: ComplianceRecord
    explanation: Explanation

class AuditManager:
    """
    Stores AI execution history, compliance report structures, policy logs, and rule evaluation ledger files.
    """
    def __init__(self) -> None:
        self.records: List[AuditRecord] = []

    def log_audit(self, record: AuditRecord) -> None:
        """
        Appends an audit record to the local list and tenant-aware file ledger on disk.
        """
        self.records.append(record)
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/governance_audit.jsonl", "a") as f:
                f.write(record.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"AuditManager: Failed to write to audit log: {e}")
