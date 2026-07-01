import time

from agents.base import BaseAgent
from app.core.context import AgentContext
from app.core.llm_provider import BaseLLMProvider
from app.intelligence.decision import DecisionEngine, WeightedEvidenceDecision
from app.schemas.evidence import (
    BaseEvidence,
    GovernmentSchemeEvidence,
    KnowledgeEvidence,
    MarketEvidence,
    MemoryEvidence,
    WeatherEvidence,
)
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResult


class VerifierAgent(BaseAgent):
    """
    VerifierAgent consolidates individual worker AgentResults, executes
    DecisionEngine reviews, and prepares the final TrustedRecommendation structure.
    """
    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        super().__init__(name="Verifier", llm_provider=llm_provider)

    async def initialize(self) -> None:
        self.state.status = "ready"

    async def execute(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        self.state.status = "running"
        self.state.start_time = time.time()

        container = context.metadata.get("container")
        if not container:
            raise ValueError("Container instance missing in AgentContext metadata scope.")

        # 1. Fetch other agent results from shared memory
        results_map = context.shared_memory.get("agent_results", {})

        # 2. Parse raw evidence from worker outcomes
        parsed_evidence: list[BaseEvidence] = []
        for name, res_json in results_map.items():
            try:
                res = AgentResult.model_validate_json(res_json)
                for ev_dict in res.evidence:
                    agent_name = ev_dict.get("agent")
                    ev: BaseEvidence
                    if agent_name == "Weather":
                        ev = WeatherEvidence.model_validate(ev_dict)
                    elif agent_name == "Market":
                        ev = MarketEvidence.model_validate(ev_dict)
                    elif agent_name == "Memory":
                        ev = MemoryEvidence.model_validate(ev_dict)
                    elif agent_name == "Knowledge":
                        ev = KnowledgeEvidence.model_validate(ev_dict)
                    elif agent_name == "GovernmentScheme":
                        ev = GovernmentSchemeEvidence.model_validate(ev_dict)
                    else:
                        ev = BaseEvidence.model_validate(ev_dict)
                    parsed_evidence.append(ev)
            except Exception as e:
                self.logger.warning(f"Verifier skipped parsing evidence for '{name}': {e!s}")

        # 3. Retrieve missing fields list
        missing_fields = context.metadata.get("missing_fields", [])

        # 4. Instantiate DecisionEngine & run evaluation
        decision_strategy = WeightedEvidenceDecision()
        engine = DecisionEngine(
            decision_strategy,
            container.arm,
            getattr(container, "policy_engine", None)
        )

        recommendation = await engine.evaluate(
            evidence_list=parsed_evidence,
            missing_fields=missing_fields,
            trace_id=context.trace_id,
            session_id=context.session_id,
            context=context
        )

        # Serialize outcome
        content_payload = recommendation.model_dump_json()

        self.state.status = "succeeded"
        self.state.end_time = time.time()
        self.state.execution_time = (self.state.end_time - self.state.start_time) * 1000.0

        return AgentResult(
            agent_name=self.name,
            content=content_payload,
            confidence=recommendation.confidence,
            metrics={"latency_ms": self.state.execution_time},
            logs=["Vetted multi-agent evidence collection under safety checks."],
            evidence=[]
        )

    async def validate(self, response: AgentResult, context: AgentContext) -> bool:
        return len(response.content) > 0

    async def cleanup(self) -> None:
        self.state.status = "cleanup"

    async def health_check(self) -> bool:
        return True
