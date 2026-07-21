import time

import pytest
from app.core.context import AgentContext
from app.knowledge.core import KnowledgePlatform
from app.knowledge.graph import KnowledgeGraph
from app.knowledge.retrieval import KnowledgeRetrievalEngine
from app.knowledge.telemetry import KnowledgeTelemetry
from app.knowledge.validation import KnowledgeValidator
from app.knowledge.vector_store import FAISSVectorStore
from app.main import app
from fastapi.testclient import TestClient


def test_knowledge_registry() -> None:
    kp = KnowledgePlatform()
    registry = kp.manager.registry

    # Test register
    mock_provider = FAISSVectorStore()
    registry.register("mock_faiss", mock_provider)
    assert "mock_faiss" in registry.list_providers()
    assert registry.get("mock_faiss") == mock_provider

    # Test deregister
    registry.deregister("mock_faiss")
    assert "mock_faiss" not in registry.list_providers()
    with pytest.raises(KeyError):
        registry.get("mock_faiss")


def test_knowledge_cache() -> None:
    kp = KnowledgePlatform()
    cache = kp.manager.cache

    cache.set("query_key", "result_data", ttl=1.0)
    assert cache.get("query_key") == "result_data"

    # Wait for TTL expiry
    time.sleep(1.1)
    assert cache.get("query_key") is None


@pytest.mark.asyncio
async def test_vector_store_adapters() -> None:
    store = FAISSVectorStore()
    await store.index_document("Rice blast treatment requires Tricyclazole chemical.", {"crop": "rice"})
    await store.index_document("Wheat rust can be managed using Propiconazole.", {"crop": "wheat"})

    assert store.get_document_count() == 2

    # Query matching Rice
    rice_results = await store.similarity_search("Rice blast treatment")
    assert len(rice_results) > 0
    assert "Tricyclazole" in rice_results[0]["content"]

    # Test filters
    filtered_results = await store.similarity_search("treatment", metadata_filter={"crop": "wheat"})
    assert len(filtered_results) == 1
    assert "wheat" in filtered_results[0]["metadata"]["crop"]


def test_knowledge_graph_traversal() -> None:
    graph = KnowledgeGraph()
    graph.add_node("farmer_a", "Farmer", {"name": "Ramu"})
    graph.add_node("crop_a", "Crop", {"name": "Wheat"})
    graph.add_node("disease_a", "Disease", {"name": "Wheat Rust"})

    graph.add_edge("farmer_a", "crop_a", "GROWING")
    graph.add_edge("crop_a", "disease_a", "SUSCEPTIBLE_TO")

    neighbors = graph.get_neighbors("farmer_a", "GROWING")
    assert len(neighbors) == 1
    assert neighbors[0]["node"]["id"] == "crop_a"

    paths = graph.find_paths("farmer_a", "disease_a")
    assert len(paths) == 1
    assert paths[0][0]["relation"] == "GROWING"
    assert paths[0][1]["relation"] == "SUSCEPTIBLE_TO"

    explanations = graph.explain_paths("farmer_a", "disease_a")
    assert len(explanations) == 1
    assert "Ramu is growing Wheat" in explanations[0]
    assert "Wheat is susceptible to Wheat Rust" in explanations[0]


@pytest.mark.asyncio
async def test_knowledge_retrieval_and_ranking() -> None:
    kp = KnowledgePlatform()
    # Populate FAISS in registry
    faiss_store = FAISSVectorStore()
    await faiss_store.index_document("Government scheme PM-Kisan provides direct money transfer.", {"id": "scheme_pm_kisan"})
    kp.manager.registry.register("faiss", faiss_store)

    engine = KnowledgeRetrievalEngine(kp)
    context = AgentContext(trace_id="test", request_id="req", session_id="sess")
    results = await engine.retrieve("PM-Kisan scheme", limit=2, context=context)

    assert len(results) > 0
    assert "PM-Kisan" in results[0]["content"]
    assert "citation" in results[0]


def test_knowledge_validator() -> None:
    validator = KnowledgeValidator()

    # Test policy compliance (banned chemicals)
    assert validator.validate_policy_compliance("Safe pesticide like Neem oil.") is True
    assert validator.validate_policy_compliance("Dangerous pesticide like Endosulfan chemical.") is False

    # Test freshness check
    fresh_meta = {"last_updated": time.time(), "authoritative": True}
    stale_meta = {"last_updated": time.time() - 31 * 24 * 3600, "authoritative": True}

    assert validator.validate_freshness(fresh_meta) is True
    assert validator.validate_freshness(stale_meta) is False


def test_knowledge_telemetry() -> None:
    from app.core.telemetry import TelemetryFramework
    framework = TelemetryFramework()
    telemetry_logger = KnowledgeTelemetry(framework)

    telemetry_logger.record_query(
        query="test query",
        latency_ms=12.5,
        results_count=2,
        cache_hit=False,
        trace_id="trace-123",
        session_id="session-456"
    )

    metrics = framework.export_metrics()
    assert metrics is not None
    # Verify our custom query metrics are stored in telemetry Framework entries list
    entries = framework._entries
    assert len(entries) > 0
    assert any(e.metric_name == "knowledge_query_latency_ms" for e in entries)


def test_api_endpoints() -> None:
    with TestClient(app) as client:
        # 1. Test status route
        response = client.get("/api/v1/knowledge/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert "health" in data
        assert "graph" in data

        # 2. Test query route
        response = client.get("/api/v1/knowledge/query?query=PM-Kisan")
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
        assert len(results) > 0
        assert "pm-kisan" in results[0]["content"].lower()

        # 3. Test index route
        response = client.post(
            "/api/v1/knowledge/index?provider=faiss",
            json={
                "content": "Newly indexed test document content",
                "metadata": {"id": "test-doc-1", "authoritative": True, "tags": ["test"]}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["document_id"] == "test-doc-1"

