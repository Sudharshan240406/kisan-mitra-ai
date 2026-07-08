import logging
import time
from typing import Any, Dict

from .document_parser import DocumentParser
from .embedding_pipeline import EmbeddingPipeline
from .publisher import Publisher
from .validation_engine import ValidationEngine
from .version_manager import VersionManager

logger = logging.getLogger("kisan_mitra_ai.knowledge_pipeline.manager")

class PipelineManager:
    """
    Coordinates self-updating knowledge pipeline phases via workflow engine pipelines.
    """
    def __init__(self, container: Any) -> None:
        self.container = container
        self.obs_mgr = getattr(container, "observability_manager", None)

        self.parser = DocumentParser()
        self.version_manager = VersionManager()
        self.validator = ValidationEngine(self.version_manager)
        self.embedding_pipeline = EmbeddingPipeline(self.obs_mgr)
        self.publisher = Publisher(getattr(container, "knowledge_platform", None))

        # Build Ingestion Workflow (Task 8: Ingestion runs via Workflow engine)
        from app.workflows import Task, Workflow
        self.ingest_workflow = Workflow(
            name="knowledge_ingestion_pipeline",
            steps=[
                Task("parse_document", self._parse_task),
                Task("validate_document", self._validate_task),
                Task("embed_document", self._embed_task),
                Task("publish_document", self._publish_task)
            ]
        )

    async def ingest_document(self, content_str: str, file_type: str, doc_id: str) -> Dict[str, Any]:
        """
        Submits and triggers the ingestion pipeline workflow.
        """
        start_time = time.time()
        logger.info(f"[PipelineManager] Triggering ingestion workflow for document '{doc_id}'")

        context = {
            "content_str": content_str,
            "file_type": file_type,
            "doc_id": doc_id
        }

        try:
            if hasattr(self.container, "workflow_manager") and self.container.workflow_manager:
                await self.container.workflow_manager.workflow_engine.execute_workflow(
                    self.ingest_workflow,
                    context
                )
            else:
                from app.workflows import WorkflowEngine
                engine = WorkflowEngine(obs_mgr=self.obs_mgr)
                await engine.execute_workflow(self.ingest_workflow, context)

            latency = (time.time() - start_time) * 1000.0
            if self.obs_mgr:
                self.obs_mgr.metrics_engine.record("ingestion_time", latency, {"doc_id": doc_id})
                self.obs_mgr.metrics_engine.record("pipeline_throughput", 1.0, {"format": file_type})

                # Fetch count of versions registered
                ver_count = sum(len(h) for h in self.version_manager.history.values())
                self.obs_mgr.metrics_engine.record("version_count", float(ver_count))

            logger.info(f"[PipelineManager] Ingestion workflow completed for document '{doc_id}' in {latency:.2f}ms")

            latest = self.version_manager.get_latest(doc_id)
            return {
                "status": "success",
                "doc_id": doc_id,
                "version": latest.version if latest else "1.0.0",
                "checksum": latest.checksum if latest else "",
                "latency_ms": latency
            }
        except Exception as e:
            logger.error(f"[PipelineManager] Ingestion workflow failed for document '{doc_id}': {e}")
            if self.obs_mgr:
                self.obs_mgr.metrics_engine.record("ingestion_failure", 1, {"doc_id": doc_id, "error": str(e)})
            raise

    # Step tasks callbacks
    async def _parse_task(self, context: Dict[str, Any]) -> None:
        doc = self.parser.parse_document(
            context["content_str"],
            context["file_type"],
            context["doc_id"]
        )
        context["parsed_doc"] = doc

    async def _validate_task(self, context: Dict[str, Any]) -> None:
        doc = context["parsed_doc"]
        report = self.validator.validate_document(doc)
        if not report.valid:
            errors_str = "; ".join(report.errors)
            raise ValueError(f"Document validation failed: {errors_str}")
        context["validation_report"] = report

    async def _embed_task(self, context: Dict[str, Any]) -> None:
        doc = context["parsed_doc"]
        chunks = self.embedding_pipeline.chunk_document(doc)
        context["chunks"] = chunks

    async def _publish_task(self, context: Dict[str, Any]) -> None:
        doc = context["parsed_doc"]
        report = context["validation_report"]
        chunks = context["chunks"]

        # Commit local metadata
        self.version_manager.register_version(doc, report.hash_checksum, status="published")

        # Publish vector indexes with latency tracking
        start_t = time.time()
        await self.publisher.publish_document(doc, chunks)
        latency = (time.time() - start_t) * 1000.0

        if self.obs_mgr:
            self.obs_mgr.metrics_engine.record("embedding_latency", latency, {"doc_id": doc.doc_id})
