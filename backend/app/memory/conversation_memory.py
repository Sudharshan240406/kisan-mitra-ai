import os
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class ConversationTurn(BaseModel):
    question: str
    intent: str
    response: str
    confidence: float
    timestamp: float
    execution_id: str

class ConversationMemoryStore:
    """
    Manages long-term dialogue exchanges logs per farmer session.
    """
    def __init__(self, data_path: str = "data/memory/conversations.json") -> None:
        self.data_path = data_path
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        self.history: Dict[str, List[ConversationTurn]] = {}
        self.load()

    def load(self) -> None:
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.history[k] = [ConversationTurn(**t) for t in v]
            except Exception:
                self.history = {}

    def save(self) -> None:
        with open(self.data_path, "w", encoding="utf-8") as f:
            data = {k: [t.model_dump() for t in v] for k, v in self.history.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_history(self, farmer_id: str) -> List[ConversationTurn]:
        return self.history.get(farmer_id, [])

    def append(self, farmer_id: str, turn: ConversationTurn) -> None:
        if farmer_id not in self.history:
            self.history[farmer_id] = []
        self.history[farmer_id].append(turn)
        
        # Keep dialogue size bounded
        if len(self.history[farmer_id]) > 50:
            self.history[farmer_id].pop(0)
            
        self.save()

    def set_history(self, farmer_id: str, history: List[ConversationTurn]) -> None:
        self.history[farmer_id] = history
        self.save()

    def clear(self, farmer_id: str) -> None:
        if farmer_id in self.history:
            del self.history[farmer_id]
            self.save()
