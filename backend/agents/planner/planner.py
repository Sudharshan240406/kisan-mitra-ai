import json
import time

from agents.base import BaseAgent
from app.core.context import AgentContext
from app.core.llm_provider import BaseLLMProvider
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResult


class PlannerAgent(BaseAgent):
    """
    Planner Agent is responsible for analyzing incoming questions and
    building a logical execution graph of worker agent dependencies.
    """
    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        super().__init__(name="Planner", llm_provider=llm_provider)

    async def initialize(self) -> None:
        self.logger.info("Initializing Planner Agent resources...")
        self.state.status = "ready"

    async def execute(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        self.state.status = "running"
        self.state.start_time = time.time()

        self.logger.info(f"Executing planning analysis on user query (Trace: {context.trace_id})...")

        query_text = request.query.lower()
        steps: list[str] = []

        # Skeleton routing decisions
        if "weather" in query_text:
            steps.append("weather")
        if "market" in query_text or "price" in query_text:
            steps.append("market")
        if "disease" in query_text or "sick" in query_text:
            steps.append("disease")

        # Default step if none match
        if not steps:
            steps.append("planner")  # Default loopback fallback

        plan = {
            "query": request.query,
            "steps": steps
        }

        # Serialize the execution plan as JSON
        content_payload = json.dumps(plan)

        self.state.status = "succeeded"
        self.state.end_time = time.time()
        self.state.execution_time = (self.state.end_time - self.state.start_time) * 1000.0

        return AgentResult(
            agent_name=self.name,
            content=content_payload,
            confidence=1.0,
            metrics={"plan_depth": len(plan["steps"]), "steps": plan["steps"]},
            logs=["Generated layout plan."]
        )

    async def validate(self, response: AgentResult, context: AgentContext) -> bool:
        try:
            plan_data = json.loads(response.content)
            return "steps" in plan_data and isinstance(plan_data["steps"], list)
        except (json.JSONDecodeError, TypeError):
            self.state.warnings.append("Planner validation failed: Invalid JSON output.")
            return False

    async def cleanup(self) -> None:
        self.logger.info("Cleaning up Planner Agent resources.")
        self.state.status = "cleanup"

    async def health_check(self) -> bool:
        return True
