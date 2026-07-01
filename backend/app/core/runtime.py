import logging
import time
from typing import Any

from app.core.context import AgentContext
from app.core.exceptions import AgentException
from app.orchestrator.registry import AgentRegistry
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResult

logger = logging.getLogger("kisan_mitra_ai")

class RuntimeManager:
    """
    Manages the runtime environment for Kisan Mitra AI agents and tools.
    Coordinates initialization, context propagation, and runtime resource cleanups.
    """
    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry
        logger.info("RuntimeManager successfully initialized.")

    async def initialize_runtime(self) -> None:
        """
        Executes initialization logic for all registered agents.
        """
        logger.info("[Runtime] Starting runtime agent initializations...")
        for name in self.registry.list_agents():
            agent = self.registry.get(name)
            logger.info(f"[Runtime] Initializing agent '{agent.name}' resources...")
            await agent.initialize()
        logger.info("[Runtime] All registered agents ready.")

    async def route_execution(
        self,
        agent_name: str,
        request: AgentRequest,
        context: AgentContext
    ) -> AgentResult:
        """
        Routes and coordinates task execution flow for a specific target agent,
        tracking telemetry metrics and logging execution lifecycles.
        """
        agent = self.registry.get(agent_name)

        # Propagate request context keys
        agent.state.metrics["current_request_id"] = context.request_id

        logger.info(
            f"[Runtime] Routing execution to agent '{agent_name}' "
            f"(Trace: {context.trace_id}, Session: {context.session_id})"
        )

        start_time = time.time()
        agent.state.status = "running"
        agent.state.start_time = start_time

        try:
            # 1. Execute agent logic
            response = await agent.execute(request, context)

            # 2. Run post-execution validation check gate
            is_valid = await agent.validate(response, context)
            if not is_valid:
                agent.state.warnings.append("Post-execution validation checks flagged output.")
                response.status = "invalid"

            # 3. Update execution duration metrics
            end_time = time.time()
            agent.state.end_time = end_time
            agent.state.status = "succeeded"
            agent.state.execution_time = (end_time - start_time) * 1000.0

            # Record execution latency in response metrics
            response.metrics["execution_latency_ms"] = agent.state.execution_time

            # Telemetry record for agent execution time
            container = context.metadata.get("container")
            if container and hasattr(container, "telemetry"):
                container.telemetry.record(
                    "agent_execution_time_ms",
                    agent.state.execution_time,
                    context.trace_id,
                    context.request_id,
                    {"agent_name": agent_name}
                )

            return response

        except Exception as e:
            end_time = time.time()
            agent.state.end_time = end_time
            agent.state.status = "failed"
            agent.state.errors.append(str(e))

            logger.error(f"[Runtime] Agent '{agent_name}' failed run: {e!s}")
            raise AgentException(f"Agent '{agent_name}' runtime crash: {e!s}")

    async def shutdown_runtime(self) -> None:
        """
        Executes cleanup tasks on all registered agents.
        """
        logger.info("[Runtime] Initiating shutdown cleanup sequence...")
        for name in self.registry.list_agents():
            agent = self.registry.get(name)
            try:
                await agent.cleanup()
                logger.info(f"[Runtime] Cleaned up agent '{name}' successfully.")
            except Exception as e:
                logger.error(f"[Runtime] Failed to clean up agent '{name}': {e!s}")

    def health(self) -> dict[str, Any]:
        """
        Exposes health metrics for the Runtime Manager.
        """
        agents_health = {}
        for name in self.registry.list_agents():
            # In a real environment we could call agent.health(),
            # but since registry.get returns BaseAgent we can query details.
            try:
                agent = self.registry.get(name)
                agents_health[name] = agent.state.status
            except Exception:
                agents_health[name] = "error"

        return {
            "status": "healthy",
            "managed_agents": list(agents_health.keys()),
            "agents_statuses": agents_health
        }
