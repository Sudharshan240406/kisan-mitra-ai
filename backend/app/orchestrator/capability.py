from typing import Any, Optional

from pydantic import BaseModel, Field


class Capability(BaseModel):
    """
    Platform capability definition mapping functionality to execution units.
    """
    capability_id: str = Field(..., description="Unique capability lookup identifier.")
    name: str = Field(..., description="Human-readable capability name.")
    version: str = Field(..., description="Capability version tracking token.")
    description: str = Field(..., description="Functional details of the capability.")
    workflow_id: str = Field(..., description="Target execution workflow template ID.")
    required_agents: list[str] = Field(default_factory=list, description="Agents participating to fulfill this capability.")
    required_tools: list[str] = Field(default_factory=list, description="Required execution client tools.")
    knowledge_sources: list[str] = Field(default_factory=list, description="Domain knowledge libraries required.")
    status: str = Field(default="healthy", description="Current health status ('healthy', 'degraded', 'unhealthy').")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata tags.")


class CapabilityRegistry:
    """
    Registry for managing and discovering platform capabilities.
    """
    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}
        self._load_default_capabilities()

    def register(self, capability: Capability) -> None:
        """
        Registers a new capability.
        """
        self._capabilities[capability.capability_id] = capability

    def discover(self, capability_id: str) -> Optional[Capability]:
        """
        Retrieves a registered capability by ID.
        """
        return self._capabilities.get(capability_id)

    def list_capabilities(self) -> list[Capability]:
        """
        Lists all registered capabilities.
        """
        return list(self._capabilities.values())

    def health_check(self) -> dict[str, Any]:
        """
        Performs diagnostic health reviews on registered capabilities.
        """
        report: dict[str, Any] = {}
        for cid, cap in self._capabilities.items():
            report[cid] = {
                "name": cap.name,
                "version": cap.version,
                "status": cap.status,
                "dependencies": {
                    "agents": cap.required_agents,
                    "tools": cap.required_tools
                }
            }
        return report

    def _load_default_capabilities(self) -> None:
        """
        Populates default platform capabilities.
        """
        self.register(Capability(
            capability_id="weather_advisory",
            name="Weather Advisory",
            version="1.0.0",
            description="Coordinates meteorological forecasts and agricultural planning warnings.",
            workflow_id="weather_workflow",
            required_agents=["Weather"],
            required_tools=["WeatherTool"]
        ))

        self.register(Capability(
            capability_id="market_intelligence",
            name="Market Intelligence",
            version="1.0.0",
            description="Tracks market prices, mandi ranges, and trading forecasts.",
            workflow_id="market_workflow",
            required_agents=["Market"],
            required_tools=["MarketTool"]
        ))

        self.register(Capability(
            capability_id="disease_diagnosis",
            name="Disease Diagnosis & Management",
            version="1.0.0",
            description="Identifies crop pathologies and matches curative guidelines.",
            workflow_id="disease_workflow",
            required_agents=["Knowledge"],
            required_tools=["KnowledgeTool"],
            knowledge_sources=["CropPathologyManuals"]
        ))

        self.register(Capability(
            capability_id="government_scheme_eligibility",
            name="Government Scheme Eligibility",
            version="1.0.0",
            description="Evaluates subsidy programs and farmer eligibility parameters.",
            workflow_id="scheme_workflow",
            required_agents=["GovernmentScheme"],
            required_tools=["GovernmentSchemeTool"]
        ))

        self.register(Capability(
            capability_id="soil_assessment",
            name="Soil Assessment & Nutrition",
            version="1.0.0",
            description="Provides analytical soil metrics and composition feedback.",
            workflow_id="soil_workflow",
            required_agents=["Soil"],
            required_tools=["SoilTool"]
        ))

        self.register(Capability(
            capability_id="irrigation_advisory",
            name="Irrigation Planning",
            version="1.0.0",
            description="Calculates water requirements and optimizes irrigation schedulers.",
            workflow_id="irrigation_workflow",
            required_agents=["Irrigation"],
            required_tools=["IrrigationTool"]
        ))
