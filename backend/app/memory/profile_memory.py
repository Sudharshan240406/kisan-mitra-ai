import os
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class FarmerProfileMemory(BaseModel):
    farmer_id: str
    preferred_language: str = "en"
    state: str = "Punjab"
    district: str = "Ludhiana"
    village: str = "Khanna"
    land: float = 2.5
    crop_history: List[str] = []
    farm_size: float = 2.5
    digital_twin_snapshot: Dict[str, Any] = {}

class ProfileMemoryStore:
    """
    Handles local disk persistence of farmer profile twin parameters.
    """
    def __init__(self, data_path: str = "data/memory/profiles.json") -> None:
        self.data_path = data_path
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        self.profiles: Dict[str, FarmerProfileMemory] = {}
        self.load()

    def load(self) -> None:
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.profiles[k] = FarmerProfileMemory(**v)
            except Exception:
                self.profiles = {}

    def save(self) -> None:
        with open(self.data_path, "w", encoding="utf-8") as f:
            data = {k: v.model_dump() for k, v in self.profiles.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get(self, farmer_id: str) -> Optional[FarmerProfileMemory]:
        return self.profiles.get(farmer_id)

    def put(self, profile: FarmerProfileMemory) -> None:
        self.profiles[profile.farmer_id] = profile
        self.save()
