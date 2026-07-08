import logging
from typing import Any, Dict

from .job_runner import JobRunner
from .queue_manager import QueueManager
from .retry_engine import RetryEngine
from .scheduler import Scheduler
from .workflow_engine import WorkflowEngine
from .workflow_registry import WorkflowRegistry

logger = logging.getLogger("kisan_mitra_ai.workflows.manager")

class WorkflowManager:
    """
    Central orchestration coordinator containing references to scheduler,
    queues, runners, engines, and registries.
    """
    def __init__(self, container: Any) -> None:
        self.container = container
        self.obs_mgr = getattr(container, "observability_manager", None)

        self.retry_engine = RetryEngine(self.obs_mgr)
        self.queue_manager = QueueManager(self.obs_mgr)
        self.scheduler = Scheduler(self)
        self.workflow_engine = WorkflowEngine(self.retry_engine, self.obs_mgr, container)
        self.registry = WorkflowRegistry(container)
        self.job_runner = JobRunner(container, self.queue_manager, self.retry_engine)

    def start(self) -> None:
        """
        Launches background scheduler loop and worker threads.
        """
        self.scheduler.start()
        self.job_runner.start()
        logger.info("[WorkflowManager] Workflow automation services initialized successfully")

    async def stop(self) -> None:
        """
        Cleans up and stops background processing loops.
        """
        await self.scheduler.stop()
        await self.job_runner.stop()
        logger.info("[WorkflowManager] Workflow automation services shutdown successfully")

    async def execute_named_workflow(self, name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Loads a registered workflow blueprint by name and executes it.
        """
        workflow = self.registry.get_workflow(name)
        if not workflow:
            raise ValueError(f"Workflow '{name}' not found in registry")
        return await self.workflow_engine.execute_workflow(workflow, context)
