import time

import pytest
from app.core.config import settings
from app.core.container import Container
from app.knowledge_engine.chunk_manager import ChunkManager
from app.knowledge_engine.citation_builder import CitationBuilder
from app.knowledge_engine.freshness import FreshnessScorer
from app.knowledge_engine.hybrid_search import HybridSearch
from app.knowledge_engine.knowledge_engine import KnowledgeEngine
from app.knowledge_engine.reranker import Reranker
from app.knowledge_engine.retriever import (
    SemanticRetriever,
    cosine_similarity,
    get_deterministic_embedding,
)
from app.orchestrator.orchestrator import AgentOrchestrator
from app.schemas.requests import ExecutionRequest


def test_deterministic_embeddings() -> None:
    """Verifies that vector generation is deterministic and unit-normalized."""
    t1 = "Organic neem pest control techniques."
    t2 = "PM-Kisan direct payment scheme details."

    v1 = get_deterministic_embedding(t1)
    v2 = get_deterministic_embedding(t1)
    v3 = get_deterministic_embedding(t2)

    assert len(v1) == 384
    assert len(v3) == 384

    # Determinism
    assert v1 == v2
    assert v1 != v3

    # Unit normalization (sum of squares is ~1.0)
    assert pytest.approx(sum(x**2 for x in v1), abs=1e-5) == 1.0
    assert pytest.approx(sum(x**2 for x in v3), abs=1e-5) == 1.0


def test_cosine_similarity() -> None:
    """Verifies vector cosine similarity boundaries."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    v3 = [1.0, 0.0, 0.0]
    v4 = [0.7071, 0.7071, 0.0]

    # Orthogonal
    assert cosine_similarity(v1, v2) == 0.0
    # Identity
    assert pytest.approx(cosine_similarity(v1, v3), abs=1e-5) == 1.0
    # 45 degrees
    assert pytest.approx(cosine_similarity(v1, v4), abs=1e-4) == 0.7071


@pytest.mark.asyncio
async def test_semantic_retriever() -> None:
    """Verifies semantic search categorisation and retrieval matching."""
    retriever = SemanticRetriever()

    # Seeded search
    results = await retriever.retrieve("PM-Kisan scheme direct payment eligibility", limit=2)
    assert len(results) > 0
    assert results[0]["document_id"] == "pm-kisan-doc"
    assert results[0]["category"] == "government_scheme"

    # Query with category filter
    faq_results = await retriever.retrieve("pest control", limit=2, category="faq")
    assert len(faq_results) == 1
    assert faq_results[0]["document_id"] == "faq-organic"


@pytest.mark.asyncio
async def test_hybrid_search() -> None:
    """Verifies keyword + semantic search fusion and weighting."""
    retriever = SemanticRetriever()
    hybrid = HybridSearch(retriever, alpha=0.6)

    # Match keyword overlap
    results = await hybrid.search("Wheat agronomic guidelines sowing vegetative", limit=2)
    assert len(results) > 0
    assert results[0]["document_id"] == "guide-wheat"
    assert results[0]["keyword_score"] > 0.0
    assert results[0]["semantic_score"] > 0.0
    # Fused score must be between semantic and keyword score bounds
    expected_score = round(0.6 * results[0]["semantic_score"] + 0.4 * results[0]["keyword_score"], 4)
    assert results[0]["score"] == pytest.approx(expected_score, abs=1e-5)


def test_freshness_scorer() -> None:
    """Verifies document freshness scoring, version prioritization, and deprecation checks."""
    scorer = FreshnessScorer(decay_period_days=100.0)
    now = time.time()

    # 1. Active valid document
    meta_active = {
        "last_updated": now - 10 * 24 * 3600,  # 10 days old
        "version": "1.2.0",
        "validity_period": {"start": now - 30 * 24 * 3600, "end": now + 30 * 24 * 3600},
        "deprecation_date": None
    }
    score_active = scorer.calculate_freshness_score(meta_active)
    assert score_active > 0.5

    # 2. Deprecated document
    meta_deprecated = meta_active.copy()
    meta_deprecated["deprecation_date"] = now - 1  # deprecated yesterday
    assert scorer.calculate_freshness_score(meta_deprecated) == 0.0

    # 3. Out-of-validity document
    meta_invalid = meta_active.copy()
    meta_invalid["validity_period"] = {"start": now + 10, "end": now + 100} # starts in the future
    assert scorer.calculate_freshness_score(meta_invalid) == 0.0

    # 4. Version boost comparison
    meta_v1 = meta_active.copy()
    meta_v1["version"] = "1.0.0"
    meta_v2 = meta_active.copy()
    meta_v2["version"] = "3.2.0"
    assert scorer.calculate_freshness_score(meta_v2) > scorer.calculate_freshness_score(meta_v1)


def test_reranker() -> None:
    """Verifies multi-criteria re-ranking pipeline ranks authoritative, fresh, and high-quality documents higher."""
    reranker = Reranker()
    now = time.time()

    docs = [
        {
            "document_id": "doc-low-quality",
            "score": 0.8,
            "metadata": {
                "document_quality": 0.3,
                "confidence": 0.8,
                "authority": "Local Farmer Blog",
                "last_updated": now,
                "version": "1.0.0"
            }
        },
        {
            "document_id": "doc-high-quality-official",
            "score": 0.8,
            "metadata": {
                "document_quality": 0.95,
                "confidence": 0.95,
                "authority": "Ministry of Agriculture",
                "last_updated": now,
                "version": "2.0.0",
                "authoritative": True
            }
        }
    ]

    ranked = reranker.rerank("irrigation guides", docs)
    assert len(ranked) == 2
    assert ranked[0]["document_id"] == "doc-high-quality-official"
    assert ranked[0]["confidence"] > ranked[1]["confidence"]
    assert "scoring_breakdown" in ranked[0]


def test_citation_builder() -> None:
    """Verifies that citations follow the required schema and contain explainability rationales."""
    builder = CitationBuilder()
    now = time.time()

    doc = {
        "document_id": "pm-kisan-doc",
        "title": "PM-Kisan Income Support Scheme",
        "section": "Eligibility and Benefits",
        "confidence": 0.965,
        "category": "government_scheme",
        "metadata": {
            "authority": "Central Government",
            "last_updated": now,
            "version": "2.1.0"
        }
    }

    citation = builder.build_citations(doc)
    assert citation["document_id"] == "pm-kisan-doc"
    assert citation["title"] == "PM-Kisan Income Support Scheme"
    assert citation["section"] == "Eligibility and Benefits"
    assert citation["confidence"] == 0.965
    assert citation["source_type"] == "government_scheme"
    assert "Source:" in citation["citation"]
    assert "PM-Kisan" in citation["explanation"]
    assert "Central Government" in citation["explanation"]


@pytest.mark.asyncio
async def test_knowledge_engine_caching() -> None:
    """Verifies query cache hits, misses, invalidations, and embedding cache interactions."""
    engine = KnowledgeEngine(default_ttl=10.0)

    # Clean state
    engine.clear_all_caches()
    assert len(engine.query_cache) == 0

    # 1. Retrieve (triggers semantic vector calculation and hybrid searches)
    q = "Neem pesticide organic"
    results = await engine.retrieve(q, limit=2)
    assert len(results) > 0

    # Query cache size should be 1
    assert len(engine.query_cache) == 1

    # 2. Retrieve again - should hit query cache
    cached_results = await engine.retrieve(q, limit=2)
    assert cached_results == results

    # Check stats or cache entries directly
    cache_key = engine.get_query_cache_key(q, 2, None)
    assert cache_key in engine.query_cache

    # 3. Invalidate query cache
    engine.invalidate_query_cache(q)
    assert cache_key not in engine.query_cache

    # 4. Check embedding cache
    text_snippet = "organic neem extract pest"
    emb = engine.retriever.get_embedding(text_snippet)
    cached_emb = engine.chunk_manager.get_embedding_from_cache(text_snippet)
    assert emb == cached_emb

    # Invalidate embedding cache
    engine.invalidate_embedding_cache(text_snippet)
    assert engine.chunk_manager.get_embedding_from_cache(text_snippet) is None


def test_chunk_manager_adaptive() -> None:
    """Verifies paragraph-based adaptive chunking and overlaps."""
    manager = ChunkManager(default_chunk_size=100, default_overlap=20)

    text = "First paragraph content here. Second paragraph content here.\n\nThird paragraph content is quite a bit longer and should split into sentences. It goes on and on. Yes indeed."
    chunks = manager.chunk_document(text, metadata={"id": "test-doc"})

    assert len(chunks) > 0
    for chunk in chunks:
        assert "content" in chunk
        assert "metadata" in chunk
        assert chunk["metadata"]["id"] == "test-doc"
        assert "chunk_index" in chunk["metadata"]


@pytest.mark.asyncio
async def test_orchestrator_integration() -> None:
    """Verifies that the AgentOrchestrator executes retrieval and injects knowledge evidence successfully."""
    container = Container(settings)
    orchestrator = AgentOrchestrator(container)

    # Stub executing a query
    req = ExecutionRequest(
        query="Tell me about the PM-Kisan scheme and who is eligible.",
        session_id="farmer_ramesh",
        farmer_id="farmer_ramesh"
    )

    res = await orchestrator.execute_query(req)
    assert res.status == "success"
    # The response payload should contain evidence of our knowledge engine intervention
    data = res.data
    assert "recommendation" in data
    # Verify that the chief agent successfully digested the evidence
    assert data["confidence"] > 0.0
