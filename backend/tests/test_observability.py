import logging
from unittest.mock import MagicMock

import pytest
from app.core.container import Container
from app.main import app
from app.observability.health_engine import HealthEngine
from app.observability.logging_engine import StructuredLoggingEngine
from app.observability.metrics_engine import MetricsEngine
from app.observability.monitoring_engine import MonitoringEngine
from app.observability.tracing_engine import TracingEngine, trace_span
from fastapi.testclient import TestClient


def test_metrics_engine():
    engine = MetricsEngine()
    engine.record("api_latency", 120.5, {"endpoint": "/api/v1/query"})
    engine.record("api_latency", 80.0)
    engine.record("agent_latency", 300.0, {"agent": "WeatherAgent"})

    metrics = engine.get_metrics()
    assert "api_latency" in metrics
    assert metrics["api_latency"]["count"] == 2
    assert metrics["api_latency"]["min"] == 80.0
    assert metrics["api_latency"]["max"] == 120.5
    assert metrics["api_latency"]["avg"] == 100.25

    assert "agent_latency" in metrics
    assert metrics["agent_latency"]["count"] == 1
    assert metrics["agent_latency"]["avg"] == 300.0

def test_tracing_engine():
    engine = TracingEngine()

    with trace_span("Parent Span", engine, trace_id="tr-test", execution_id="ex-test") as parent:
        assert parent.trace_id == "tr-test"
        assert parent.execution_id == "ex-test"

        with trace_span("Child Span", engine) as child:
            assert child.trace_id == "tr-test"
            assert child.parent_span_id == parent.span_id

    traces = engine.get_traces()
    assert len(traces) == 2
    assert traces[0]["name"] == "Child Span"
    assert traces[1]["name"] == "Parent Span"
    assert traces[0]["parent_span_id"] == traces[1]["span_id"]

def test_structured_logging_engine():
    engine = StructuredLoggingEngine()
    engine.log(
        level=logging.INFO,
        message="Test info log",
        trace_id="tr-log",
        execution_id="ex-log",
        agent="MarketAgent",
        latency_ms=150.0,
        confidence=0.92
    )

    logs = engine.get_logs()
    assert len(logs) == 1
    assert logs[0]["message"] == "Test info log"
    assert logs[0]["trace_id"] == "tr-log"
    assert logs[0]["agent"] == "MarketAgent"
    assert logs[0]["latency_ms"] == 150.0
    assert logs[0]["confidence"] == 0.92

def test_alert_rules():
    mock_manager = MagicMock()
    mock_manager.logging_engine = MagicMock()
    engine = MonitoringEngine(mock_manager)

    # 1. High Latency Alert
    engine.check_alert_rules("api_call", "tr-1", "ex-1", {"latency_ms": 6000.0})
    assert len(engine.alerts) == 1
    assert engine.alerts[0].rule_name == "High Latency"

    # 2. Agent Crash
    engine.check_alert_rules("agent_failure", "tr-2", "ex-2", {"agent_name": "WeatherAgent", "error": "LLM timed out"})
    assert len(engine.alerts) == 2
    assert engine.alerts[1].rule_name == "Agent Crash"

    # 3. Repeated Failures
    engine.check_alert_rules("agent_run", "tr-3", "ex-3", {"agent_name": "MarketAgent", "success": False})
    engine.check_alert_rules("agent_run", "tr-3", "ex-3", {"agent_name": "MarketAgent", "success": False})
    engine.check_alert_rules("agent_run", "tr-3", "ex-3", {"agent_name": "MarketAgent", "success": False})
    assert any(a.rule_name == "Repeated Failures" for a in engine.alerts)

    # 4. External API Failure
    engine.check_alert_rules("IntegrationFailed", "tr-4", "ex-4", {"integration_id": "IMDWeatherAdapter", "error": "HTTP 500"})
    assert any(a.rule_name == "External API Failure" for a in engine.alerts)

    # 5. Low Confidence Spike
    engine.check_alert_rules("chief_agent", "tr-5", "ex-5", {"confidence": 0.4})
    engine.check_alert_rules("chief_agent", "tr-5", "ex-5", {"confidence": 0.3})
    engine.check_alert_rules("chief_agent", "tr-5", "ex-5", {"confidence": 0.4})
    assert any(a.rule_name == "Low Confidence Spike" for a in engine.alerts)

@pytest.mark.anyio
async def test_health_engine():
    container = Container()
    engine = HealthEngine(container)
    health = await engine.check_health()
    assert "database" in health
    assert "redis" in health
    assert "vector_db" in health
    assert "gemini" in health
    assert "scheduler" in health
    assert "notification_engine" in health
    assert "memory_engine" in health
    assert "knowledge_engine" in health
    assert "overall_status" in health

def test_api_endpoints():
    with TestClient(app) as client:
        # 1. Test metrics endpoint
        res = client.get("/api/v1/observability/metrics")
        assert res.status_code == 200
        assert isinstance(res.json(), dict)

        # 2. Test health endpoint
        res = client.get("/api/v1/observability/health")
        assert res.status_code == 200
        assert "database" in res.json()

        # 3. Test traces endpoint
        res = client.get("/api/v1/observability/traces")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

        # 4. Test system_status endpoint
        res = client.get("/api/v1/observability/system_status")
        assert res.status_code == 200
        assert "cpu_percent" in res.json()
