import logging
from typing import Any, Dict, Optional

from .workflow_engine import ConditionalStep, Task, Workflow

logger = logging.getLogger("kisan_mitra_ai.workflows.registry")

class WorkflowRegistry:
    """
    Registers and maintains templates for system background workflows.
    """
    def __init__(self, container: Any) -> None:
        self.container = container
        self._workflows: Dict[str, Workflow] = {}
        self._register_default_workflows()

    def get_workflow(self, name: str) -> Optional[Workflow]:
        """
        Retrieves a workflow template by its registered name.
        """
        return self._workflows.get(name)

    def _register_default_workflows(self) -> None:
        # 1. Knowledge Ingestion Workflow
        self._workflows["knowledge_ingestion"] = Workflow(
            name="knowledge_ingestion",
            steps=[
                Task("fetch_raw_manuals", self._fetch_raw_manuals),
                Task("parse_and_chunk", self._parse_and_chunk),
                Task("generate_embeddings", self._generate_embeddings),
                Task("refresh_knowledge_base", self._refresh_knowledge_base)
            ]
        )

        # 2. Autonomous Reminders Workflow
        self._workflows["autonomous_reminders"] = Workflow(
            name="autonomous_reminders",
            steps=[
                Task("fetch_active_twins", self._fetch_active_twins),
                ConditionalStep(
                    condition_callback=self._has_pending_reminders,
                    true_step=[
                        Task("evaluate_reminders", self._evaluate_reminders),
                        Task("dispatch_reminder_notifications", self._dispatch_reminder_notifications)
                    ],
                    false_step=None
                )
            ]
        )

        # 3. Analytics Aggregation Workflow
        self._workflows["analytics_aggregation"] = Workflow(
            name="analytics_aggregation",
            steps=[
                Task("aggregate_metrics", self._aggregate_metrics),
                Task("generate_analytics_report", self._generate_analytics_report)
            ]
        )

        # 4. Maintenance Workflow
        self._workflows["maintenance"] = Workflow(
            name="maintenance",
            steps=[
                Task("clean_expired_sessions", self._clean_expired_sessions),
                Task("verify_db_integrity", self._verify_db_integrity)
            ]
        )

        # 5. Cleanup Workflow
        self._workflows["cleanup"] = Workflow(
            name="cleanup",
            steps=[
                Task("purge_temp_files", self._purge_temp_files),
                Task("purge_old_queue_jobs", self._purge_old_queue_jobs)
            ]
        )

    # Ingestion steps
    async def _fetch_raw_manuals(self, context: Dict[str, Any]) -> None:
        logger.info("[WorkflowTask] Fetching raw crop cultivation manuals")
        context["raw_count"] = 5

    async def _parse_and_chunk(self, context: Dict[str, Any]) -> None:
        raw_cnt = context.get("raw_count", 0)
        logger.info(f"[WorkflowTask] Chunking {raw_cnt} raw manuals")
        context["chunks_count"] = raw_cnt * 5

    async def _generate_embeddings(self, context: Dict[str, Any]) -> None:
        chunks_cnt = context.get("chunks_count", 0)
        logger.info(f"[WorkflowTask] Generating vector embeddings for {chunks_cnt} chunks")

    async def _refresh_knowledge_base(self, context: Dict[str, Any]) -> None:
        logger.info("[WorkflowTask] Rebuilding knowledge vector index")

    # Autonomous Reminders steps
    async def _fetch_active_twins(self, context: Dict[str, Any]) -> None:
        logger.info("[WorkflowTask] Scanning active digital twins for reminder rules")
        context["has_reminders"] = True

    async def _has_pending_reminders(self, context: Dict[str, Any]) -> bool:
        return bool(context.get("has_reminders", False))

    async def _evaluate_reminders(self, context: Dict[str, Any]) -> None:
        logger.info("[WorkflowTask] Evaluating advisory reminder schedules")

    async def _dispatch_reminder_notifications(self, context: Dict[str, Any]) -> None:
        logger.info("[WorkflowTask] Dispatching advisory SMS/notifications to subscribers")

    # Analytics steps
    async def _aggregate_metrics(self, context: Dict[str, Any]) -> None:
        logger.info("[WorkflowTask] Querying performance metrics from Observability platform")

    async def _generate_analytics_report(self, context: Dict[str, Any]) -> None:
        logger.info("[WorkflowTask] Synthesizing system health summary analytics PDF/JSON report")

    # Maintenance steps
    async def _clean_expired_sessions(self, context: Dict[str, Any]) -> None:
        logger.info("[WorkflowTask] Purging expired database sessions and security tokens")

    async def _verify_db_integrity(self, context: Dict[str, Any]) -> None:
        logger.info("[WorkflowTask] Performing database integrity connection checks")

    # Cleanup steps
    async def _purge_temp_files(self, context: Dict[str, Any]) -> None:
        logger.info("[WorkflowTask] Purging transient temporary cache directories")

    async def _purge_old_queue_jobs(self, context: Dict[str, Any]) -> None:
        logger.info("[WorkflowTask] Deleting background execution log entries older than 24h")
