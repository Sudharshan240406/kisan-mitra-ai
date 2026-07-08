import asyncio
import time
from typing import Any, Dict

import pytest
from app.main import app
from app.workflows.queue_manager import QueueManager
from app.workflows.retry_engine import RetryEngine
from app.workflows.scheduler import Scheduler
from app.workflows.workflow_engine import (
    ConditionalStep,
    ParallelStep,
    Task,
    Workflow,
    WorkflowEngine,
)
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_workflow_engine_sequential() -> None:
    # 1. Test basic sequential execution
    context = {"val": 1}

    def add_one(ctx: Dict[str, Any]) -> None:
        ctx["val"] += 1

    def multiply_two(ctx: Dict[str, Any]) -> None:
        ctx["val"] *= 2

    task1 = Task("add_one", add_one)
    task2 = Task("multiply_two", multiply_two)

    engine = WorkflowEngine()
    workflow = Workflow("seq_wf", [task1, task2])

    result = await engine.execute_workflow(workflow, context)

    assert result["val"] == 4

@pytest.mark.asyncio
async def test_workflow_engine_conditional_and_parallel() -> None:
    context = {"score": 80, "visited_true": False, "visited_false": False, "parallel_count": 0}

    def cond_callback(ctx: Dict[str, Any]) -> bool:
        return bool(ctx["score"] >= 75)

    def true_cb(ctx: Dict[str, Any]) -> None:
        ctx["visited_true"] = True

    def false_cb(ctx: Dict[str, Any]) -> None:
        ctx["visited_false"] = True

    def parallel_cb(ctx: Dict[str, Any]) -> None:
        ctx["parallel_count"] += 1

    task_true = Task("true_task", true_cb)
    task_false = Task("false_task", false_cb)

    p_task1 = Task("p1", parallel_cb)
    p_task2 = Task("p2", parallel_cb)

    cond_step = ConditionalStep(cond_callback, task_true, task_false)
    parallel_step = ParallelStep([p_task1, p_task2])

    engine = WorkflowEngine()
    workflow = Workflow("cond_parallel_wf", [cond_step, parallel_step])

    result = await engine.execute_workflow(workflow, context)

    assert result["visited_true"] is True
    assert result["visited_false"] is False
    assert result["parallel_count"] == 2

@pytest.mark.asyncio
async def test_workflow_timeout() -> None:
    # Test task timeout limits
    async def slow_cb(ctx: Dict[str, Any]) -> None:
        await asyncio.sleep(1.0)

    task = Task("slow_task", slow_cb, timeout=0.1)
    engine = WorkflowEngine()
    workflow = Workflow("timeout_wf", [task])

    with pytest.raises(TimeoutError):
        await engine.execute_workflow(workflow, {})

def test_retry_engine_and_dlq() -> None:
    retry_eng = RetryEngine()

    # 1. Check failure logging
    retry_eng.log_failure("job_123", "Connection lost", "notification")
    assert len(retry_eng.failure_log) == 1
    assert retry_eng.failure_log[0]["entity_id"] == "job_123"

    # 2. Check Dead Letter Queue (DLQ)
    retry_eng.move_to_dlq("job_123", {"msg": "hello"}, "Max retries exceeded", "notification")
    assert len(retry_eng.dlq) == 1
    assert retry_eng.dlq[0]["error"] == "Max retries exceeded"

def test_scheduler_cron_calculation() -> None:
    scheduler = Scheduler()

    # Standard cron: 'minute hour day-of-month month day-of-week'
    # Test matching: '*/5 * * * *'
    now = time.time()
    next_run = scheduler._calculate_next_cron("*/5 * * * *", now)

    # Should be in the future, multiple of 5 minutes
    assert next_run > now

    # Test range match
    assert scheduler._match_field("1-10", 5) is True
    assert scheduler._match_field("1-10", 15) is False

    # Test list match
    assert scheduler._match_field("1,15,30", 15) is True
    assert scheduler._match_field("1,15,30", 20) is False

@pytest.mark.asyncio
async def test_queue_manager_enqueuing() -> None:
    qm = QueueManager()

    # Enqueue a job
    job_id = await qm.enqueue("notification", {"recipient": "+9199999", "message": "Weather warning"})

    assert job_id is not None
    assert qm.get_queue_depth() == 1

    job = qm.get_job(job_id)
    assert job is not None
    assert job.job_type == "notification"
    assert job.status == "pending"

def test_e2e_orchestrator_background_enqueuing() -> None:
    with TestClient(app) as client:
        # Submit a query request with background=True
        payload = {
            "session_id": "test_sess_99",
            "query": "Is rain expected tomorrow?",
            "background": True,
            "farmer_id": "farmer_ramesh"
        }

        # Test endpoint
        resp = client.post("/api/v1/query", json=payload)

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "job_id" in data["data"]
        assert data["data"]["status"] == "queued"
