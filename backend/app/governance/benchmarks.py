import logging
import time
from typing import Any, Callable

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.governance.benchmarks")


class BenchmarkResult(BaseModel):
    """
    Single benchmark execution result record.
    """
    name: str = Field(..., description="Benchmark test name.")
    component: str = Field(..., description="Target component benchmarked.")
    iterations: int = Field(..., description="Number of iterations executed.")
    avg_latency_ms: float = Field(..., description="Average latency in milliseconds.")
    min_latency_ms: float = Field(..., description="Minimum observed latency.")
    max_latency_ms: float = Field(..., description="Maximum observed latency.")
    throughput_ops_sec: float = Field(..., description="Operations per second throughput.")


class BenchmarkReport(BaseModel):
    """
    Aggregate benchmark results report.
    """
    total_benchmarks: int = 0
    results: list[BenchmarkResult] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)
    summary: str = ""


class BenchmarkRunner:
    """
    Performance benchmarking runner profiling core platform components.
    """

    def __init__(self) -> None:
        self._benchmarks: dict[str, Callable[[], None]] = {}

    def register_benchmark(self, name: str, component: str, func: Callable[[], None]) -> None:
        """
        Registers a benchmark function for profiling.
        """
        self._benchmarks[name] = func

    def run_benchmark(
        self,
        name: str,
        component: str,
        func: Callable[[], None],
        iterations: int = 100
    ) -> BenchmarkResult:
        """
        Runs a single benchmark and records timing results.
        """
        timings: list[float] = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            elapsed = (time.perf_counter() - start) * 1000  # ms
            timings.append(elapsed)

        avg = sum(timings) / len(timings)
        min_t = min(timings)
        max_t = max(timings)
        throughput = 1000.0 / avg if avg > 0 else 0.0

        return BenchmarkResult(
            name=name,
            component=component,
            iterations=iterations,
            avg_latency_ms=round(avg, 4),
            min_latency_ms=round(min_t, 4),
            max_latency_ms=round(max_t, 4),
            throughput_ops_sec=round(throughput, 2)
        )

    def run_all(self, iterations: int = 100) -> BenchmarkReport:
        """
        Runs all registered benchmarks and aggregates results.
        """
        results: list[BenchmarkResult] = []
        for name, func in self._benchmarks.items():
            result = self.run_benchmark(name, name, func, iterations)
            results.append(result)
            logger.info(f"Benchmark '{name}': avg={result.avg_latency_ms}ms, throughput={result.throughput_ops_sec} ops/s")

        return BenchmarkReport(
            total_benchmarks=len(results),
            results=results,
            summary=f"Completed {len(results)} benchmarks."
        )

    @staticmethod
    def create_platform_benchmarks() -> "BenchmarkRunner":
        """
        Factory method creating a runner pre-loaded with core platform benchmarks.
        """
        runner = BenchmarkRunner()

        # Planner benchmark (simulated)
        def bench_planner() -> None:
            data: dict[str, Any] = {"intents": ["weather"], "confidence": 0.9}
            _ = list(data.values())

        runner.register_benchmark("planner_resolution", "Planner", bench_planner)

        # Workflow engine benchmark (simulated)
        def bench_workflow() -> None:
            steps = ["Planner", "Weather", "Verifier"]
            _ = [s.upper() for s in steps]

        runner.register_benchmark("workflow_execution", "WorkflowEngine", bench_workflow)

        # Decision engine benchmark (simulated)
        def bench_decision() -> None:
            scores = [0.8, 0.7, 0.9, 0.6]
            _ = sum(scores) / len(scores)

        runner.register_benchmark("decision_evaluation", "DecisionEngine", bench_decision)

        # Conversation state machine benchmark (simulated)
        def bench_conversation() -> None:
            states = ["Greeting", "Intent", "Context", "Recommendation", "Closure"]
            _ = {s: i for i, s in enumerate(states)}

        runner.register_benchmark("conversation_transitions", "ConversationStateMachine", bench_conversation)

        # Policy engine benchmark (simulated)
        def bench_policy() -> None:
            policies = [{"scope": "global", "rules": ["r1", "r2"]}]
            _ = [p for p in policies if p.get("scope") == "global"]

        runner.register_benchmark("policy_evaluation", "PolicyEngine", bench_policy)

        # Reasoning graph benchmark (simulated)
        def bench_graph() -> None:
            nodes: dict[str, list[str]] = {"root": ["n1", "n2"], "n1": ["n3"], "n2": [], "n3": []}
            visited: set[str] = set()
            stack = ["root"]
            while stack:
                node = stack.pop()
                if node not in visited:
                    visited.add(node)
                    stack.extend(nodes.get(node, []))

        runner.register_benchmark("reasoning_graph_traversal", "ReasoningGraph", bench_graph)

        # Telemetry recording benchmark (simulated)
        def bench_telemetry() -> None:
            metrics: dict[str, float] = {}
            for i in range(10):
                metrics[f"metric_{i}"] = float(i) * 1.1

        runner.register_benchmark("telemetry_recording", "TelemetryFramework", bench_telemetry)

        return runner
