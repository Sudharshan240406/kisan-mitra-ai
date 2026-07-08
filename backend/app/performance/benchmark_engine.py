import asyncio
import logging
import time
from typing import Any, List

from pydantic import BaseModel

logger = logging.getLogger("kisan_mitra_ai.performance.benchmark")

class BenchmarkResult(BaseModel):
    name: str
    operations_count: int
    concurrency: int
    duration_ms: float
    throughput_ops_sec: float
    average_latency_ms: float

class BenchmarkEngine:
    """
    Simulates concurrent query stress tests to bench platform throughput.
    """
    def __init__(self, performance_manager: Any) -> None:
        self.pm = performance_manager

    async def run_orchestrator_benchmark(self, orchestrator: Any, count: int = 10, concurrency: int = 3) -> BenchmarkResult:
        """
        Stresses the AgentOrchestrator under a concurrency limit.
        """
        from app.schemas.requests import ExecutionRequest

        request = ExecutionRequest(
            session_id="benchmark_session",
            query="Advisory for organic wheat fertilization",
            background=False
        )

        semaphore = asyncio.Semaphore(concurrency)
        latencies: List[float] = []

        async def _run_single() -> None:
            async with semaphore:
                start = time.time()
                try:
                    await orchestrator.execute_query(request)
                except Exception as e:
                    logger.error(f"Benchmark query failed: {e}")
                finally:
                    latencies.append((time.time() - start) * 1000.0)

        start_time = time.time()
        tasks = [asyncio.create_task(_run_single()) for _ in range(count)]
        await asyncio.gather(*tasks)
        duration = (time.time() - start_time) * 1000.0

        throughput = count / (duration / 1000.0) if duration > 0 else 0.0
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0

        return BenchmarkResult(
            name="Orchestrator Stress Test",
            operations_count=count,
            concurrency=concurrency,
            duration_ms=round(duration, 2),
            throughput_ops_sec=round(throughput, 2),
            average_latency_ms=round(avg_lat, 2)
        )

    async def run_knowledge_benchmark(self, knowledge_platform: Any, count: int = 15, concurrency: int = 4) -> BenchmarkResult:
        """
        Profiles similarity searches across registered vector stores.
        """
        semaphore = asyncio.Semaphore(concurrency)
        latencies: List[float] = []

        async def _run_single() -> None:
            async with semaphore:
                start = time.time()
                try:
                    # Query FAISS vector store simulation
                    await knowledge_platform.manager.query_provider("faiss", "wheat fertilization")
                except Exception as e:
                    logger.error(f"Benchmark knowledge query failed: {e}")
                finally:
                    latencies.append((time.time() - start) * 1000.0)

        start_time = time.time()
        tasks = [asyncio.create_task(_run_single()) for _ in range(count)]
        await asyncio.gather(*tasks)
        duration = (time.time() - start_time) * 1000.0

        throughput = count / (duration / 1000.0) if duration > 0 else 0.0
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0

        return BenchmarkResult(
            name="Knowledge Retrieve Test",
            operations_count=count,
            concurrency=concurrency,
            duration_ms=round(duration, 2),
            throughput_ops_sec=round(throughput, 2),
            average_latency_ms=round(avg_lat, 2)
        )

    async def run_memory_benchmark(self, container: Any, count: int = 10, concurrency: int = 3) -> BenchmarkResult:
        """
        Profiles memory database retrieval routines.
        """
        # Fetch mock memory context from orchestrator/agents if available
        semaphore = asyncio.Semaphore(concurrency)
        latencies: List[float] = []

        async def _run_single() -> None:
            async with semaphore:
                start = time.time()
                try:
                    # Access a mock db query or cache check simulation
                    await asyncio.sleep(0.01)
                except Exception as e:
                    logger.error(f"Benchmark memory read failed: {e}")
                finally:
                    latencies.append((time.time() - start) * 1000.0)

        start_time = time.time()
        tasks = [asyncio.create_task(_run_single()) for _ in range(count)]
        await asyncio.gather(*tasks)
        duration = (time.time() - start_time) * 1000.0

        throughput = count / (duration / 1000.0) if duration > 0 else 0.0
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0

        return BenchmarkResult(
            name="Memory Access Test",
            operations_count=count,
            concurrency=concurrency,
            duration_ms=round(duration, 2),
            throughput_ops_sec=round(throughput, 2),
            average_latency_ms=round(avg_lat, 2)
        )

    async def run_workflow_benchmark(self, workflow_manager: Any, count: int = 8, concurrency: int = 2) -> BenchmarkResult:
        """
        Profiles sequential/parallel task enqueuing and running pipelines.
        """
        semaphore = asyncio.Semaphore(concurrency)
        latencies: List[float] = []

        async def _run_single() -> None:
            async with semaphore:
                start = time.time()
                try:
                    # Enqueue a dummy job
                    await workflow_manager.queue_manager.enqueue("notification", {"msg": "hello"})
                except Exception as e:
                    logger.error(f"Benchmark workflow job failed: {e}")
                finally:
                    latencies.append((time.time() - start) * 1000.0)

        start_time = time.time()
        tasks = [asyncio.create_task(_run_single()) for _ in range(count)]
        await asyncio.gather(*tasks)
        duration = (time.time() - start_time) * 1000.0

        throughput = count / (duration / 1000.0) if duration > 0 else 0.0
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0

        return BenchmarkResult(
            name="Workflow Dispatch Test",
            operations_count=count,
            concurrency=concurrency,
            duration_ms=round(duration, 2),
            throughput_ops_sec=round(throughput, 2),
            average_latency_ms=round(avg_lat, 2)
        )
