import asyncio
import logging
from typing import Any

from app.core.context import AgentContext
from app.core.exceptions import OrchestratorException
from app.orchestrator.registry import AgentRegistry
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResult
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai")

class ScheduledTask(BaseModel):
    """
    Metadata representation of a task to be scheduled and run.
    """
    task_id: str = Field(..., description="Unique ID for this task step.")
    agent_name: str = Field(..., description="Target worker agent to execute.")
    request: AgentRequest = Field(..., description="Input parameters and query for the agent.")
    dependencies: list[str] = Field(default_factory=list, description="IDs of tasks that must finish before this runs.")
    priority: int = Field(0, description="Priority weight (higher is run first).")
    max_retries: int = Field(3, description="Maximum retry limit on failure.")

class ExecutionScheduler:
    """
    Infrastructure Scheduler managing agent task graphs.
    Supports sequential flows, parallel runs, and dependency DAG execution.
    """
    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry
        logger.info("ExecutionScheduler initialized.")

    async def schedule_sequential(
        self,
        tasks: list[ScheduledTask],
        context: AgentContext
    ) -> list[AgentResult]:
        """
        Executes a list of scheduled tasks one after the other.
        """
        results: list[AgentResult] = []
        logger.info(f"[Scheduler] Starting sequential execution of {len(tasks)} tasks (Trace: {context.trace_id}).")

        for task in sorted(tasks, key=lambda x: x.priority, reverse=True):
            response = await self._execute_task_with_retry(task, context)
            results.append(response)

        return results

    async def schedule_parallel(
        self,
        tasks: list[ScheduledTask],
        context: AgentContext
    ) -> list[AgentResult]:
        """
        Executes a list of scheduled tasks in parallel concurrently.
        """
        logger.info(f"[Scheduler] Starting parallel execution of {len(tasks)} tasks (Trace: {context.trace_id}).")
        coroutines = [self._execute_task_with_retry(task, context) for task in tasks]
        results = await asyncio.gather(*coroutines)
        return list(results)

    async def execute_dag(
        self,
        tasks: list[ScheduledTask],
        context: AgentContext
    ) -> dict[str, AgentResult]:
        """
        Executes tasks by resolving dependency constraints (DAG execution).
        Uses a dynamic asyncio task execution loop.
        """
        logger.info(f"[Scheduler] Starting DAG execution of {len(tasks)} tasks (Trace: {context.trace_id}).")

        # Maps task_id -> task
        task_map = {t.task_id: t for t in tasks}

        # Build dependency mappings
        in_degree = {t.task_id: len(t.dependencies) for t in tasks}
        adjacency_list: dict[str, list[str]] = {t.task_id: [] for t in tasks}
        for t in tasks:
            for dep in t.dependencies:
                if dep in adjacency_list:
                    adjacency_list[dep].append(t.task_id)

        # Track completed tasks and their return values
        completed_results: dict[str, AgentResult] = {}

        # Set of tasks currently executing
        running_tasks: set[str] = set()

        async def run_single_task(task_id: str) -> None:
            task = task_map[task_id]
            # Context propagation: we can copy context memory values as dependencies finish
            # For framework validation, we just merge memory contexts
            logger.info(f"[Scheduler] DAG Node '{task_id}' start prerequisites complete.")
            response = await self._execute_task_with_retry(task, context)

            # Record result
            completed_results[task_id] = response
            running_tasks.remove(task_id)

            # Decrement dependency counters of children
            for child in adjacency_list[task_id]:
                in_degree[child] -= 1

        # Execution loop
        while len(completed_results) < len(tasks):
            # Find tasks with 0 dependencies that aren't running or done
            ready_tasks = [
                tid for tid, deg in in_degree.items()
                if deg == 0 and tid not in completed_results and tid not in running_tasks
            ]

            if not ready_tasks and not running_tasks:
                # Cycle detected
                raise OrchestratorException("Circular dependency detected in ScheduledTask graph.")

            # Start execution for all ready tasks
            for tid in ready_tasks:
                running_tasks.add(tid)
                asyncio.create_task(run_single_task(tid))

            # Yield control to allow tasks to complete
            await asyncio.sleep(0.005)

        logger.info(f"[Scheduler] DAG execution completed for trace {context.trace_id}.")
        return completed_results

    async def _execute_task_with_retry(self, task: ScheduledTask, context: AgentContext) -> AgentResult:
        """
        Executes a scheduled task by fetching its agent from the registry,
        handling error retry loops.
        """
        agent = self.registry.get(task.agent_name)
        retries = 0

        while True:
            try:
                # Core execute invocation
                return await agent.execute(task.request, context)
            except Exception as e:
                retries += 1
                logger.warning(
                    f"[Scheduler] Task '{task.task_id}' failed (Attempt {retries}/{task.max_retries}): {e!s}"
                )
                if retries >= task.max_retries:
                    logger.error(f"[Scheduler] Task '{task.task_id}' exceeded max retries.")
                    # Return error payload
                    return AgentResult(
                        agent_name=task.agent_name,
                        content=f"Error executing task: {e!s}",
                        status="failed",
                        metrics={"error": str(e), "retries": retries}
                    )
                # Quick wait before retry
                await asyncio.sleep(0.01)

    def health(self) -> dict[str, Any]:
        """
        Exposes health metrics for the Scheduler.
        """
        return {
            "status": "healthy",
            "scheduler_class": self.__class__.__name__,
            "features_supported": ["sequential", "parallel", "dag_resolver"]
        }
