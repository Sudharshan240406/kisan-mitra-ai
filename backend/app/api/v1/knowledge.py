import logging
import time
from typing import Any, Optional

from app.core.container import Container
from app.core.context import AgentContext
from app.dependencies.container import get_container
from app.knowledge.retrieval import KnowledgeRetrievalEngine
from app.knowledge.telemetry import KnowledgeTelemetry
from app.knowledge.validation import KnowledgeValidator
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/knowledge", tags=["Agricultural Knowledge Platform"])
logger = logging.getLogger("kisan_mitra_ai.api.knowledge")


@router.get("/status", response_model=dict[str, Any])
async def get_knowledge_status(
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Retrieve live health status, registered providers, cache statistics, and graph node/edge counts.
    """
    logger.info("Fetching Knowledge Platform status info.")
    kp = container.knowledge_platform
    health_info = kp.health()

    # Enrich with graph counts
    graph = getattr(kp, "graph", None)
    graph_info = graph.health() if graph else {"status": "missing"}

    return {
        "status": "active",
        "health": health_info,
        "graph": graph_info,
        "timestamp": time.time()
    }


@router.get("/query", response_model=list[dict[str, Any]])
async def query_knowledge_base(
    query: str = Query(..., description="Semantic or keyword query text to search for."),
    limit: int = Query(5, ge=1, le=20, description="Max results limit."),
    crop: Optional[str] = Query(None, description="Boost/filter results by crop type context."),
    location: Optional[str] = Query(None, description="Boost/filter results by location context."),
    container: Container = Depends(get_container)
) -> list[dict[str, Any]]:
    """
    Query the Hybrid Knowledge Retrieval Engine using semantic search, vector stores, and relational models.
    """
    start_time = time.time()
    logger.info(f"Querying Knowledge Platform: '{query}' (crop={crop}, location={location})")

    kp = container.knowledge_platform
    engine = KnowledgeRetrievalEngine(kp)
    validator = KnowledgeValidator()
    telemetry_logger = KnowledgeTelemetry(container.telemetry)

    # Set up dummy context parameters to mock query variables
    context = AgentContext(
        trace_id="api-trace-id",
        request_id=f"api-req-{int(start_time)}",
        session_id="api-session-id",
        language="en"
    )
    context.crop = crop
    context.location = location

    # Fetch results
    results = await engine.retrieve(query, limit=limit, context=context)

    # Filter/validate results
    validated_results = []
    for res in results:
        if validator.validate_all(res):
            validated_results.append(res)
        else:
            logger.warning(f"Document failed validation: {res.get('id')}")

    # Track telemetry
    latency_ms = (time.time() - start_time) * 1000.0
    cache_hit = False  # Simply calculated inside manager, but for api we track retrieval latency
    telemetry_logger.record_query(
        query=query,
        latency_ms=latency_ms,
        results_count=len(validated_results),
        cache_hit=cache_hit,
        trace_id=context.trace_id,
        session_id=context.session_id,
        metadata={"crop": crop, "location": location}
    )

    return validated_results


class IndexRequest(BaseModel):
    content: str
    metadata: dict[str, Any]


@router.post("/index", response_model=dict[str, Any])
async def index_knowledge_document(
    payload: IndexRequest,
    provider: str = Query("faiss", description="Target vector store database key."),
    container: Container = Depends(get_container)
) -> dict[str, Any]:
    """
    Ingest a new document, manual segment, or scheme policy into the swappable Vector store indexes.
    """
    content = payload.content
    metadata = payload.metadata
    logger.info(f"Indexing new document into provider '{provider}'")
    kp = container.knowledge_platform
    try:
        store = kp.manager.registry.get(provider)
        await store.index_document(content, metadata)

        # Log version history
        from app.knowledge.core import KnowledgeMetadata
        doc_id = metadata.get("id", f"doc-{int(time.time())}")
        doc_meta = KnowledgeMetadata(
            id=doc_id,
            source=provider,
            version=metadata.get("version", "1.0.0"),
            tags=metadata.get("tags", []),
            extra=metadata
        )
        kp.manager.version_manager.register_version(doc_meta)

        return {"status": "success", "provider": provider, "document_id": doc_id}
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Provider '{provider}' is not a registered vector store.")
    except Exception as e:
        logger.error(f"Failed to index document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
