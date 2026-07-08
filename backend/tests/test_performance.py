import asyncio
import time

import pytest
from app.core.config import settings
from app.core.container import Container
from app.main import app
from app.performance.benchmark_engine import BenchmarkEngine
from app.performance.cache_engine import CacheEngine
from app.performance.concurrency_manager import ConcurrencyManager
from app.performance.rate_limiter import RateLimiter
from app.performance.resource_pool import ResourcePool
from fastapi.testclient import TestClient


def test_cache_engine_operations() -> None:
    cache = CacheEngine(default_ttl=0.2)

    # 1. Basic Set & Get
    cache.set("key1", "val1")
    assert cache.get("key1") == "val1"
    assert cache.stats["hits"] == 1
    assert cache.stats["misses"] == 0

    # 2. TTL Expiry
    time.sleep(0.3)
    assert cache.get("key1") is None
    assert cache.stats["misses"] == 1

    # 3. Invalidation
    cache.set("key2", "val2")
    cache.invalidate("key2")
    assert cache.get("key2") is None

@pytest.mark.asyncio
async def test_resource_pool_capacity() -> None:
    # Pool size: 2
    pool = ResourcePool(factory=lambda: "mock_conn", max_size=2)

    # Acquire 2 resources
    r1 = await pool.acquire()
    r2 = await pool.acquire()

    assert r1.resource == "mock_conn"
    assert r2.resource == "mock_conn"
    assert pool.get_utilization() == 1.0

    # Third acquisition should be blocked
    # Let's wrap in a timeout to verify it blocks
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(pool.acquire(), timeout=0.1)

    # Release one resource and acquire again
    await pool.release(r1.resource)
    assert pool.get_utilization() == 0.5

    r3 = await pool.acquire()
    assert r3.resource == "mock_conn"

@pytest.mark.asyncio
async def test_concurrency_manager() -> None:
    mgr = ConcurrencyManager(default_limit=2)

    # Set up mock tasks with sleep
    async def task_cb(i: int) -> int:
        await asyncio.sleep(0.05)
        return i

    tasks = [task_cb(i) for i in range(5)]
    start = time.time()
    results = await mgr.execute_parallel(tasks)
    duration = time.time() - start

    assert len(results) == 5
    assert results == [0, 1, 2, 3, 4]
    # Under limit 2, 5 tasks of 50ms should take at least ~100-150ms
    assert duration >= 0.1

def test_rate_limiter_throttling() -> None:
    # Limiter: capacity = 3, refill rate = 1 token/sec
    limiter = RateLimiter(capacity=3, refill_rate=1.0)

    # Allow 3 bursts
    assert limiter.is_allowed("ip:127.0.0.1") is True
    assert limiter.is_allowed("ip:127.0.0.1") is True
    assert limiter.is_allowed("ip:127.0.0.1") is True

    # 4th request should be blocked
    assert limiter.is_allowed("ip:127.0.0.1") is False

    # Wait for refill
    time.sleep(1.1)
    assert limiter.is_allowed("ip:127.0.0.1") is True

@pytest.mark.asyncio
async def test_benchmark_engine_runs() -> None:
    container = Container(settings)
    pm = container.performance_manager
    benchmark = BenchmarkEngine(pm)

    # Mock components for benchmark test
    from app.orchestrator.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator(container)

    res_orch = await benchmark.run_orchestrator_benchmark(orchestrator, count=2, concurrency=1)
    assert res_orch.operations_count == 2
    assert res_orch.concurrency == 1
    assert res_orch.duration_ms > 0
    assert res_orch.throughput_ops_sec >= 0

    res_know = await benchmark.run_knowledge_benchmark(container.knowledge_platform, count=2, concurrency=1)
    assert res_know.operations_count == 2

    res_workflow = await benchmark.run_workflow_benchmark(container.workflow_manager, count=2, concurrency=1)
    assert res_workflow.operations_count == 2

def test_e2e_orchestrator_caching_and_rate_limiting() -> None:
    with TestClient(app) as client:
        # Submit query
        payload = {
            "session_id": "perf_test_sess",
            "query": "What is the nitrogen dose for maize?",
            "background": False
        }

        # 1. Verify response is served
        resp1 = client.post("/api/v1/query", json=payload)
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["status"] == "success"

        # 2. Verify second query hits cache and is served quickly
        start = time.time()
        resp2 = client.post("/api/v1/query", json=payload)
        dur = (time.time() - start) * 1000.0
        assert resp2.status_code == 200

        # Cached latency should be extremely low
        assert dur < 250.0

        # 3. Test rate limiting throttling by triggering bursts
        # The limiter default capacity is 25, let's make 30 requests to trigger throttling (429)
        throttled = False
        for _ in range(35):
            resp = client.post("/api/v1/query", json=payload)
            if resp.status_code == 429:
                throttled = True
                break

        assert throttled is True
