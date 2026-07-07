import os
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class RecommendationRecord(BaseModel):
    recommended_schemes: List[str] = Field(default_factory=list)
    applied_schemes: List[str] = Field(default_factory=list)
    rejected_schemes: List[str] = Field(default_factory=list)
    completed_schemes: List[str] = Field(default_factory=list)
    documents_requested: List[str] = Field(default_factory=list)
    documents_submitted: List[str] = Field(default_factory=list)

class RecommendationMemoryStore:
    """
    Manages structured yojana eligibility application steps history.
    """
    def __init__(self, data_path: str = "data/memory/recommendations.json") -> None:
        self.data_path = data_path
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        self.records: Dict[str, RecommendationRecord] = {}
        self.load()

    def load(self) -> None:
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.records[k] = RecommendationRecord(**v)
            except Exception:
                self.records = {}

    def save(self) -> None:
        with open(self.data_path, "w", encoding="utf-8") as f:
            data = {k: v.model_dump() for k, v in self.records.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get(self, farmer_id: str) -> RecommendationRecord:
        if farmer_id not in self.records:
            self.records[farmer_id] = RecommendationRecord()
        return self.records[farmer_id]

    def put(self, farmer_id: str, record: RecommendationRecord) -> None:
        self.records[farmer_id] = record
        self.save()

    def clear(self, farmer_id: str) -> None:
        if farmer_id in self.records:
            del self.records[farmer_id]
            self.save()
