from abc import ABC, abstractmethod
from typing import Any, Optional

from app.core.llm_provider import BaseLLMProvider
from app.intelligence.analysis import QueryAnalysis
from app.intelligence.intent import IntentType
from app.orchestrator.capability import Capability, CapabilityRegistry
from pydantic import BaseModel, Field


class ExecutionPlan(BaseModel):
    """
    Structured execution recipe mapping query intents/entities to orchestrated agent nodes.
    """
    workflow_id: str = Field(..., description="Target workflow template ID.")
    required_agents: list[str] = Field(..., description="Agent list required to execute this plan.")
    required_tools: list[str] = Field(..., description="Tool list required by agents during execution.")
    knowledge_sources: list[str] = Field(default_factory=list, description="RAG manual collections consulted.")
    execution_order: list[str] = Field(..., description="Topological sequence steps for task execution.")
    parallel_groups: list[list[str]] = Field(default_factory=list, description="Tasks that can be executed concurrently in parallel.")
    dependencies: dict[str, list[str]] = Field(default_factory=dict, description="Task prerequisites resolver index.")
    timeout: int = Field(default=30, description="Maximum allowed duration in seconds before graph timeout.")
    retry_policy: dict[str, Any] = Field(
        default_factory=lambda: {"max_retries": 3, "backoff": "exponential"},
        description="Retry specifications for node steps."
    )
    priority: int = Field(default=0, description="Execution priority weight (higher is run first).")
    estimated_complexity: str = Field(default="low", description="Estimated plan complexity level ('low', 'moderate', 'high').")

class PlanningStrategy(ABC):
    """
    Abstract interface for graph planners mapping user QueryAnalysis to ExecutionPlans.
    """
    @abstractmethod
    async def plan(self, analysis: QueryAnalysis) -> ExecutionPlan:
        """
        Formulate an ExecutionPlan based on intents and entities.
        """
        pass

class RuleBasedPlanner(PlanningStrategy):
    """
    Provider-independent rule planner mapping recognized intent categories to workflow templates.
    """
    def __init__(self, capability_registry: Optional[CapabilityRegistry] = None) -> None:
        self.capability_registry = capability_registry

    async def plan(self, analysis: QueryAnalysis) -> ExecutionPlan:  # noqa: PLR0912
        intents = analysis.intents.detected_intents

        # 1. Check if CapabilityRegistry is available to dynamically resolve capabilities
        if self.capability_registry:
            requested_caps = []
            if IntentType.WEATHER in intents:
                requested_caps.append("weather_advisory")
            if IntentType.MARKET in intents:
                requested_caps.append("market_intelligence")
            if IntentType.DISEASE in intents:
                requested_caps.append("disease_diagnosis")
            if IntentType.GOVERNMENT_SCHEME in intents:
                requested_caps.append("government_scheme_eligibility")
            if IntentType.SOIL in intents:
                requested_caps.append("soil_assessment")

            # Resolve capabilities
            resolved_caps: list[Capability] = []
            for cap_id in requested_caps:
                cap = self.capability_registry.discover(cap_id)
                if cap:
                    resolved_caps.append(cap)

            if len(resolved_caps) > 1:
                # Mixed workflow case
                agents: list[str] = ["Planner"]
                tools: list[str] = []
                sources: list[str] = []
                parallel: list[list[str]] = []
                sub_agents = []
                for cap in resolved_caps:
                    for a in cap.required_agents:
                        if a not in sub_agents:
                            sub_agents.append(a)
                    for t in cap.required_tools:
                        if t not in tools:
                            tools.append(t)
                    for s in cap.knowledge_sources:
                        if s not in sources:
                            sources.append(s)

                agents.extend(sub_agents)
                parallel.append(sub_agents)
                order = ["Planner", *sub_agents, "Verifier"]
                agents.append("Verifier")
                deps = {}
                for idx in range(1, len(order)):
                    deps[order[idx]] = [order[idx - 1]]

                return ExecutionPlan(
                    workflow_id="mixed_workflow",
                    required_agents=agents,
                    required_tools=tools,
                    knowledge_sources=sources,
                    execution_order=order,
                    parallel_groups=parallel,
                    dependencies=deps,
                    priority=10,
                    estimated_complexity="high"
                )
            elif len(resolved_caps) == 1:
                # Single capability case
                cap = resolved_caps[0]
                agents = ["Planner"]
                for a in cap.required_agents:
                    if a not in agents:
                        agents.append(a)
                agents.append("Verifier")
                order = ["Planner", *cap.required_agents, "Verifier"]
                deps = {}
                for idx in range(1, len(order)):
                    deps[order[idx]] = [order[idx - 1]]

                return ExecutionPlan(
                    workflow_id=cap.workflow_id,
                    required_agents=agents,
                    required_tools=cap.required_tools,
                    knowledge_sources=cap.knowledge_sources,
                    execution_order=order,
                    parallel_groups=[],
                    dependencies=deps,
                    priority=5,
                    estimated_complexity="moderate" if cap.knowledge_sources else "low"
                )

        # Default fallback values (if no registry or no matching capabilities resolved)
        wf_id = "unknown_workflow"
        agents = ["Planner"]
        tools = []
        sources = []
        order = ["Planner"]
        parallel = []
        deps = {}
        priority = 0
        complexity = "low"

        # 2. Resolve intents to workflows
        if IntentType.MIXED_QUERY in intents:
            wf_id = "mixed_workflow"
            agents = ["Planner"]
            tools = []
            order = ["Planner"]

            # Map sub-intents
            sub_agents = []
            if IntentType.WEATHER in intents:
                sub_agents.append("Weather")
                tools.append("WeatherTool")
            if IntentType.MARKET in intents:
                sub_agents.append("Market")
                tools.append("MarketTool")
            if IntentType.DISEASE in intents:
                sub_agents.append("Knowledge")
                tools.append("KnowledgeTool")
                sources.append("CropPathologyManuals")

            agents.extend(sub_agents)
            # Parallel run group
            parallel.append(sub_agents)
            # Order: Planner -> Workers (in parallel) -> Verifier
            order.extend(sub_agents)
            agents.append("Verifier")
            order.append("Verifier")

            complexity = "high"
            priority = 10

        elif IntentType.WEATHER in intents:
            wf_id = "weather_workflow"
            agents = ["Planner", "Weather", "Verifier"]
            tools = ["WeatherTool"]
            order = ["Planner", "Weather", "Verifier"]
            complexity = "low"

        elif IntentType.DISEASE in intents:
            wf_id = "disease_workflow"
            agents = ["Planner", "Knowledge", "Verifier"]
            tools = ["KnowledgeTool"]
            sources = ["CropPathologyManuals"]
            order = ["Planner", "Knowledge", "Verifier"]
            complexity = "moderate"

        elif IntentType.MARKET in intents:
            wf_id = "market_workflow"
            agents = ["Planner", "Market", "Verifier"]
            tools = ["MarketTool"]
            order = ["Planner", "Market", "Verifier"]
            complexity = "low"

        elif IntentType.GOVERNMENT_SCHEME in intents:
            wf_id = "scheme_workflow"
            agents = ["Planner", "GovernmentScheme", "Verifier"]
            tools = ["GovernmentSchemeTool"]
            order = ["Planner", "GovernmentScheme", "Verifier"]
            complexity = "moderate"

        # Build dependency mappings matching execution order
        for idx in range(1, len(order)):
            deps[order[idx]] = [order[idx - 1]]

        return ExecutionPlan(
            workflow_id=wf_id,
            required_agents=agents,
            required_tools=tools,
            knowledge_sources=sources,
            execution_order=order,
            parallel_groups=parallel,
            dependencies=deps,
            priority=priority,
            estimated_complexity=complexity
        )

# Future-facing swappable planning strategies
class HybridPlanner(PlanningStrategy):
    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None) -> None:
        self.llm_provider = llm_provider

    async def plan(self, analysis: QueryAnalysis) -> ExecutionPlan:
        # First generate base rule plan
        base_plan = await RuleBasedPlanner().plan(analysis)
        if not self.llm_provider:
            return base_plan

        # Use LLM to optimize/refine the base plan execution order or parallel groups
        prompt = (
            f"Optimize this agricultural execution plan for query: '{analysis.raw_query}'\n"
            f"Base Plan: {base_plan.model_dump_json()}\n"
            "Output the updated JSON plan only, maintaining the exact schema."
        )
        try:
            res = self.llm_provider.generate(prompt)
            clean_res = res.strip()
            if clean_res.startswith("```"):
                lines = clean_res.splitlines()
                clean_lines = [line for line in lines if not line.startswith("```")]
                clean_res = "\n".join(clean_lines).strip()
            import json
            data = json.loads(clean_res)
            return ExecutionPlan.model_validate(data)
        except Exception:
            return base_plan

class LLMPlanner(PlanningStrategy):
    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None) -> None:
        self.llm_provider = llm_provider

    async def plan(self, analysis: QueryAnalysis) -> ExecutionPlan:
        # If no LLM provider is injected, fallback to RuleBasedPlanner
        if not self.llm_provider:
            return await RuleBasedPlanner().plan(analysis)

        prompt = (
            f"Given the user query: '{analysis.raw_query}'\n"
            f"Detected intents: {analysis.intents.detected_intents}\n"
            f"Detected entities: {analysis.entities.entities}\n"
            "Formulate a structured execution plan as a JSON object matching this schema:\n"
            "{\n"
            "  \"workflow_id\": \"string\",\n"
            "  \"required_agents\": [\"string\"],\n"
            "  \"required_tools\": [\"string\"],\n"
            "  \"knowledge_sources\": [\"string\"],\n"
            "  \"execution_order\": [\"string\"],\n"
            "  \"parallel_groups\": [[\"string\"]],\n"
            "  \"dependencies\": {\"step_name\": [\"dep1\"]},\n"
            "  \"timeout\": 30,\n"
            "  \"priority\": 0,\n"
            "  \"estimated_complexity\": \"low\" | \"moderate\" | \"high\"\n"
            "}\n"
            "Output ONLY the JSON object, without formatting backticks."
        )
        try:
            res = self.llm_provider.generate(prompt)
            # Clean response markdown backticks if any
            clean_res = res.strip()
            if clean_res.startswith("```"):
                lines = clean_res.splitlines()
                clean_lines = [line for line in lines if not line.startswith("```")]
                clean_res = "\n".join(clean_lines).strip()
            import json
            data = json.loads(clean_res)
            return ExecutionPlan.model_validate(data)
        except Exception:
            # Fallback on parsing/generation failure
            return await RuleBasedPlanner().plan(analysis)

class FutureMLPlanner(PlanningStrategy):
    async def plan(self, analysis: QueryAnalysis) -> ExecutionPlan:
        # Simulates a machine learning classifier routing queries based on lexical features
        query = analysis.raw_query.lower()
        required_agents = ["Planner"]
        order = ["Planner"]

        # Simple keyword weight mapping
        agent_weights = {
            "weather": ["weather", "rain", "temperature", "forecast", "climate"],
            "market": ["price", "mandi", "market", "cost", "sell", "inr"],
            "disease": ["sick", "disease", "pest", "fungus", "spot", "leaf"]
        }

        for agent, keywords in agent_weights.items():
            if any(kw in query for kw in keywords):
                if agent not in required_agents:
                    required_agents.append(agent)
                    order.append(agent)

        return ExecutionPlan(
            workflow_id="ml_derived_workflow",
            required_agents=required_agents,
            required_tools=[],
            knowledge_sources=[],
            execution_order=order,
            parallel_groups=[],
            dependencies={},
            timeout=30,
            priority=len(required_agents),
            estimated_complexity="moderate" if len(required_agents) > 2 else "low"
        )
