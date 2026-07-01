from typing import Any

from pydantic import BaseModel, Field


class MarketPrice(BaseModel):
    """
    Agricultural ontology model representing market price indexing data.
    """
    price_id: str = Field(..., description="Unique pricing record identifier.")
    market_name: str = Field(..., description="Target market/mandi node name.")
    state: str = Field(..., description="State region designation.")
    district: str = Field(..., description="District subdivision region.")
    commodity: str = Field(..., description="Commodity type catalog classification.")
    variety: str = Field(..., description="Specific crop variety type.")
    grade: str = Field("FAQ", description="Mandi commodity quality grade (e.g., FAQ, Fine, Superfine).")
    min_price: float = Field(..., description="Lowest trading price for the commodity record.")
    max_price: float = Field(..., description="Highest trading price for the commodity record.")
    modal_price: float = Field(..., description="Modal/average trading price for the commodity record.")
    unit: str = Field("Quintal", description="Standard metric unit of mass measurement (e.g., Quintal, Kg).")
    timestamp: float = Field(..., description="Mandi transaction date record timestamp.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible JSON metadata parameters.")
