import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger("kisan_mitra_ai.workflows.engine")

class Task:
    """
    Individual atomic unit of work inside a workflow.
    """
    def __init__(
        self,
        name: str,
        callback: Callable[..., Any],
        timeout: Optional[float] = None,
        retry_policy: Optional[Dict[str, Any]] = None
    ) -> None:
        self.name = name
        self.callback = callback
        self.timeout = timeout
        self.retry_policy = retry_policy or {}

class ParallelStep:
    """
    Wraps a collection of Tasks to execute concurrently.
    """
    def __init__(self, tasks: List[Task]) -> None:
        self.tasks = tasks

class ConditionalStep:
    """
    Selects true_step or false_step depending on condition callback evaluation.
    """
    def __init__(
        self,
        condition_callback: Callable[..., Any],
        true_step: Optional[Any] = None,
        false_step: Optional[Any] = None
    ) -> None:
        self.condition_callback = condition_callback
        self.true_step = true_step
        self.false_step = false_step

class Workflow:
    """
    A collection of tasks, parallel steps, and conditional branches executed in order.
    """
    def __init__(self, name: str, steps: List[Union[Task, ParallelStep, ConditionalStep]]) -> None:
        self.name = name
        self.steps = steps

class WorkflowEngine:
    """
    Core engine parsing and running workflows, logging latency to the metrics collector.
    """
    def __init__(self, retry_engine: Any = None, obs_mgr: Any = None) -> None:
        self.retry_engine = retry_engine
        self.obs_mgr = obs_mgr

    async def execute_workflow(self, workflow: Workflow, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a workflow end-to-end, keeping track of overall latency.
        """
        start_time = time.time()
        logger.info(f"[WorkflowEngine] Starting execution of workflow '{workflow.name}'")
        try:
            for step in workflow.steps:
                await self._execute_step(step, context)

            latency = (time.time() - start_time) * 1000.0
            if self.obs_mgr:
                self.obs_mgr.metrics_engine.record("workflow_latency", latency, {"workflow": workflow.name})

            logger.info(f"[WorkflowEngine] Workflow '{workflow.name}' completed successfully in {latency:.2f}ms")
            return context
        except Exception as e:
            latency = (time.time() - start_time) * 1000.0
            logger.error(f"[WorkflowEngine] Workflow '{workflow.name}' failed after {latency:.2f}ms: {e}")
            raise

    async def _execute_step(self, step: Any, context: Dict[str, Any]) -> None:
        if isinstance(step, Task):
            await self._execute_task_with_retry(step, context)
        elif isinstance(step, ParallelStep):
            logger.info(f"[WorkflowEngine] Executing {len(step.tasks)} tasks in parallel")
            await asyncio.gather(*(self._execute_task_with_retry(t, context) for t in step.tasks))
        elif isinstance(step, ConditionalStep):
            if asyncio.iscoroutinefunction(step.condition_callback):
                cond = await step.condition_callback(context)
            else:
                cond = step.condition_callback(context)

            logger.info(f"[WorkflowEngine] Condition callback evaluated to: {cond}")
            next_step = step.true_step if cond else step.false_step
            if next_step:
                if isinstance(next_step, list):
                    for sub_step in next_step:
                        await self._execute_step(sub_step, context)
                else:
                    await self._execute_step(next_step, context)

    async def _execute_task_with_retry(self, task: Task, context: Dict[str, Any]) -> None:
        policy = task.retry_policy
        max_retries = policy.get("max_retries", 0)
        initial_delay = policy.get("initial_delay", 1.0)
        backoff_factor = policy.get("backoff_factor", 2.0)

        attempt = 0
        while True:
            try:
                await self._execute_task(task, context)
                return
            except Exception as e:
                attempt += 1
                if attempt > max_retries:
                    logger.error(f"[WorkflowEngine] Task '{task.name}' failed after {attempt} attempts: {e}")
                    raise

                delay = initial_delay * (backoff_factor ** (attempt - 1))
                logger.warning(f"[WorkflowEngine] Task '{task.name}' failed. Retrying attempt {attempt}/{max_retries} in {delay:.2f}s... Error: {e}")

                if self.obs_mgr:
                    self.obs_mgr.metrics_engine.record("retry_count", 1, {"task": task.name})

                await asyncio.sleep(delay)

    async def _execute_task(self, task: Task, context: Dict[str, Any]) -> None:
        logger.info(f"[WorkflowEngine] Running task '{task.name}'")
        start_t = time.time()
        try:
            if asyncio.iscoroutinefunction(task.callback):
                coro = task.callback(context)
            else:
                loop = asyncio.get_running_loop()
                coro = loop.run_in_executor(None, task.callback, context)

            if task.timeout:
                await asyncio.wait_for(coro, timeout=task.timeout)
            else:
                await coro

            logger.info(f"[WorkflowEngine] Task '{task.name}' completed in {(time.time() - start_t)*1000:.2f}ms")
        except asyncio.TimeoutError:
            logger.error(f"[WorkflowEngine] Task '{task.name}' timed out after {task.timeout}s")
            raise TimeoutError(f"Task '{task.name}' timed out after {task.timeout}s")
        except Exception as e:
            logger.error(f"[WorkflowEngine] Task '{task.name}' failed: {e}")
            raise
