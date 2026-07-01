import os
from typing import Any

import pytest
from app.governance.benchmarks import BenchmarkRunner
from app.governance.engine import GovernanceEngine
from app.governance.models import ModelMetadata, ModelRegistry
from app.governance.plugins import IPlugin, PluginMetadata, PluginRegistry
from app.governance.prompts import PromptMetadata, PromptRegistry
from app.governance.validators import PlatformValidator

# ── Plugin Framework Tests ──────────────────────────────────────────


class MockPlugin(IPlugin):
    """Test plugin for verification."""
    def __init__(self, plugin_id: str = "test-plugin", version: str = "1.0.0") -> None:
        self._metadata = PluginMetadata(
            plugin_id=plugin_id,
            name="Test Plugin",
            version=version,
            description="A test plugin for verification.",
            capabilities=["test_cap"],
            agents=["TestAgent"],
            services=["TestService"],
            tools=["TestTool"],
            dependencies=[],
            status="active"
        )

    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata

    async def initialize(self) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def health_check(self) -> bool:
        return True


def test_plugin_registry_register_and_discover() -> None:
    registry = PluginRegistry()
    plugin = MockPlugin()
    registry.register(plugin)

    found = registry.discover("test-plugin")
    assert found is not None
    assert found.metadata.name == "Test Plugin"
    assert found.metadata.version == "1.0.0"


def test_plugin_registry_deregister() -> None:
    registry = PluginRegistry()
    registry.register(MockPlugin())
    registry.deregister("test-plugin")
    assert registry.discover("test-plugin") is None


def test_plugin_registry_version_conflict() -> None:
    registry = PluginRegistry()
    registry.register(MockPlugin(version="1.0.0"))
    with pytest.raises(ValueError, match="Version conflict"):
        registry.register(MockPlugin(version="2.0.0"))


@pytest.mark.asyncio
async def test_plugin_registry_health_check() -> None:
    registry = PluginRegistry()
    registry.register(MockPlugin())
    report = await registry.health_check()
    assert "test-plugin" in report
    assert report["test-plugin"]["healthy"] is True


# ── Model Registry Tests ────────────────────────────────────────────


def test_model_registry_register_and_discover() -> None:
    registry = ModelRegistry()
    model = ModelMetadata(
        model_id="test-model",
        name="Test Model",
        provider="Local",
        version="1.0.0",
        capabilities=["text-generation"]
    )
    registry.register(model)

    found = registry.discover("test-model")
    assert found is not None
    assert found.provider == "Local"


def test_model_registry_load_from_config() -> None:
    config_path = os.path.join(os.path.dirname(__file__), "..", "app", "config", "models.json")
    registry = ModelRegistry()
    registry.load_from_config(config_path)
    models = registry.list_models()
    assert len(models) >= 4


# ── Prompt Registry Tests ───────────────────────────────────────────


def test_prompt_registry_register_and_discover() -> None:
    registry = PromptRegistry()
    prompt = PromptMetadata(
        prompt_id="test-prompt",
        version="1.0.0",
        description="Test prompt.",
        template="Hello {name}",
        variables=["name"]
    )
    registry.register(prompt)

    found = registry.discover("test-prompt")
    assert found is not None
    assert found.template == "Hello {name}"


def test_prompt_registry_versioning() -> None:
    registry = PromptRegistry()
    registry.register(PromptMetadata(prompt_id="p1", version="1.0.0", description="V1", template="T1"))
    registry.register(PromptMetadata(prompt_id="p1", version="2.0.0", description="V2", template="T2"))

    # Latest version
    latest = registry.discover("p1")
    assert latest is not None
    assert latest.version == "2.0.0"

    # Specific version
    v1 = registry.discover("p1", version="1.0.0")
    assert v1 is not None
    assert v1.template == "T1"

    assert registry.get_versions("p1") == ["1.0.0", "2.0.0"]


def test_prompt_registry_deprecation() -> None:
    registry = PromptRegistry()
    registry.register(PromptMetadata(prompt_id="dep", version="1.0.0", description="Test", template="T"))
    registry.deprecate("dep", "1.0.0", "Replaced by v2")

    prompt = registry.discover("dep", "1.0.0")
    assert prompt is not None
    assert prompt.status == "deprecated"
    assert prompt.deprecation_notes == "Replaced by v2"


def test_prompt_registry_load_from_config() -> None:
    config_path = os.path.join(os.path.dirname(__file__), "..", "app", "config", "prompts.json")
    registry = PromptRegistry()
    registry.load_from_config(config_path)
    prompts = registry.list_prompts()
    assert len(prompts) >= 6


# ── Governance Engine Tests ─────────────────────────────────────────


def test_governance_engine_register_and_report() -> None:
    engine = GovernanceEngine()
    engine.register_artifact("plugin", "p1", "1.0.0")
    engine.register_artifact("model", "m1", "2.0.0")
    engine.register_artifact("prompt", "pr1", "1.0.0", status="draft")

    report = engine.generate_report()
    assert report.total_artifacts == 3
    assert report.active_count == 2
    assert report.draft_count == 1
    assert report.artifact_breakdown["plugin"] == 1


def test_governance_engine_deprecation() -> None:
    engine = GovernanceEngine()
    engine.register_artifact("workflow", "wf1", "1.0.0")
    engine.deprecate_artifact("workflow", "wf1", "Replaced")

    rec = engine.get_artifact("workflow", "wf1")
    assert rec is not None
    assert rec.status == "deprecated"


def test_governance_engine_version_upgrade() -> None:
    engine = GovernanceEngine()
    engine.register_artifact("model", "m1", "1.0.0")
    engine.register_artifact("model", "m1", "2.0.0")

    rec = engine.get_artifact("model", "m1")
    assert rec is not None
    assert rec.version == "2.0.0"
    assert rec.previous_version == "1.0.0"


# ── Architecture Validator Tests ────────────────────────────────────


def test_architecture_validator_clean() -> None:
    validator = PlatformValidator()
    report = validator.validate_architecture(
        agent_names=["Weather", "Market"],
        capability_ids=["weather_advisory", "market_intelligence"],
        workflow_ids=["weather_workflow", "market_workflow"],
        service_names=["WeatherService", "MarketService"],
        plugin_ids=[]
    )
    assert report.report_type == "architecture"
    assert report.failed_checks == 0


def test_architecture_validator_detects_duplicate_capability() -> None:
    validator = PlatformValidator()
    report = validator.validate_architecture(
        agent_names=["Weather"],
        capability_ids=["weather_advisory", "weather_advisory"],
        workflow_ids=["weather_workflow"],
        service_names=["WeatherService"],
        plugin_ids=[]
    )
    error_issues = [i for i in report.issues if i.severity == "error"]
    assert len(error_issues) == 1
    assert error_issues[0].category == "duplicate_capability"


def test_circular_dependency_detection() -> None:
    validator = PlatformValidator()
    graph: dict[str, list[str]] = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A"],  # circular
    }
    issues = validator.detect_circular_dependencies(graph)
    circular = [i for i in issues if i.category == "circular_dependency"]
    assert len(circular) >= 1


def test_integration_chain_validation() -> None:
    validator = PlatformValidator()
    capabilities: list[dict[str, Any]] = [
        {"capability_id": "weather_advisory", "workflow_id": "weather_workflow", "required_agents": ["Weather"]},
        {"capability_id": "market_intelligence", "workflow_id": "market_workflow", "required_agents": ["Market"]},
    ]
    workflows: list[dict[str, Any]] = [
        {"workflow_id": "weather_workflow", "steps": ["Planner", "Weather", "Verifier"]},
        {"workflow_id": "market_workflow", "steps": ["Planner", "Market", "Verifier"]},
    ]
    report = validator.validate_integration_chain(
        capabilities=capabilities,
        workflows=workflows,
        agent_names=["Weather", "Market", "Planner", "Verifier"]
    )
    assert report.report_type == "integration"
    assert report.failed_checks == 0


def test_integration_chain_detects_broken_workflow_ref() -> None:
    validator = PlatformValidator()
    capabilities: list[dict[str, Any]] = [
        {"capability_id": "broken_cap", "workflow_id": "nonexistent_workflow", "required_agents": ["Weather"]},
    ]
    workflows: list[dict[str, Any]] = [
        {"workflow_id": "weather_workflow", "steps": ["Planner", "Weather", "Verifier"]},
    ]
    report = validator.validate_integration_chain(
        capabilities=capabilities,
        workflows=workflows,
        agent_names=["Weather"]
    )
    error_issues = [i for i in report.issues if i.severity == "error"]
    assert len(error_issues) == 1
    assert error_issues[0].category == "broken_reference"


# ── Benchmark Runner Tests ──────────────────────────────────────────


def test_benchmark_runner_single() -> None:
    runner = BenchmarkRunner()
    result = runner.run_benchmark("test_bench", "TestComponent", lambda: None, iterations=50)
    assert result.iterations == 50
    assert result.avg_latency_ms >= 0
    assert result.throughput_ops_sec > 0


def test_benchmark_runner_platform() -> None:
    runner = BenchmarkRunner.create_platform_benchmarks()
    report = runner.run_all(iterations=10)
    assert report.total_benchmarks == 7
    assert len(report.results) == 7
    for result in report.results:
        assert result.avg_latency_ms >= 0
