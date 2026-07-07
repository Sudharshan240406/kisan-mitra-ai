import logging
import time
from typing import Any, Dict, List, Optional, cast

from app.knowledge_engine.chunk_manager import ChunkManager
from app.knowledge_engine.citation_builder import CitationBuilder
from app.knowledge_engine.freshness import FreshnessScorer
from app.knowledge_engine.hybrid_search import HybridSearch
from app.knowledge_engine.reranker import Reranker
from app.knowledge_engine.retriever import SemanticRetriever

logger = logging.getLogger("kisan_mitra_ai.knowledge_engine.knowledge_engine")

class KnowledgeEngine:
    """
    Unified entry point for the Knowledge Intelligence Engine.
    Exposes APIs for retrieval, searching, reranking, freshness calculation, and citations.
    Integrates query and embedding caching with invalidation hooks.
    """
    def __init__(self, default_ttl: float = 300.0) -> None:
        self.chunk_manager: ChunkManager = ChunkManager()
        self.retriever: SemanticRetriever = SemanticRetriever(chunk_manager=self.chunk_manager)
        self.hybrid_search: HybridSearch = HybridSearch(semantic_retriever=self.retriever)
        self.freshness_scorer: FreshnessScorer = FreshnessScorer()
        self.rerank_engine: Reranker = Reranker(freshness_scorer=self.freshness_scorer)
        self.citation_builder: CitationBuilder = CitationBuilder()

        self.default_ttl = default_ttl
        # Query Cache: Maps query keys to {"value": results, "expires_at": float}
        self.query_cache: Dict[str, Dict[str, Any]] = {}

    def get_query_cache_key(self, query: str, limit: int, category: Optional[str]) -> str:
        return f"query:{query}:limit:{limit}:category:{category or 'all'}"

    def check_query_cache(self, key: str) -> Optional[List[Dict[str, Any]]]:
        entry = self.query_cache.get(key)
        if entry:
            if entry["expires_at"] > time.time():
                logger.debug(f"Query Cache HIT for key: {key}")
                return entry["value"]  # type: ignore[no-any-return]
            else:
                logger.debug(f"Query Cache EXPIRED for key: {key}")
                del self.query_cache[key]
        return None

    def set_query_cache(self, key: str, value: List[Dict[str, Any]], ttl: Optional[float] = None) -> None:
        cache_ttl = ttl if ttl is not None else self.default_ttl
        self.query_cache[key] = {
            "value": value,
            "expires_at": time.time() + cache_ttl
        }
        logger.debug(f"Query Cache SET for key: {key} (TTL: {cache_ttl}s)")

    def invalidate_query_cache(self, query: Optional[str] = None) -> None:
        if query is None:
            self.query_cache.clear()
            logger.info("Query Cache cleared completely.")
        else:
            prefix = f"query:{query}:"
            keys_to_del = [k for k in self.query_cache if k.startswith(prefix)]
            for k in keys_to_del:
                del self.query_cache[k]
            logger.info(f"Query Cache invalidated for query: '{query}' ({len(keys_to_del)} entries removed).")

    def invalidate_embedding_cache(self, text: Optional[str] = None) -> None:
        if text is None:
            self.chunk_manager.clear_embedding_cache()
            logger.info("Embedding Cache cleared completely.")
        else:
            self.chunk_manager.invalidate_embedding(text)
            logger.info("Embedding Cache invalidated for text snippet.")

    def clear_all_caches(self) -> None:
        self.invalidate_query_cache()
        self.invalidate_embedding_cache()

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        category: Optional[str] = None,
        context: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Coordinates full retrieval pipeline: hybrid search, freshness filters, re-ranking, and citation building.
        """
        # Resolve category if context points to a crop
        search_category = category
        if not search_category and context and hasattr(context, "metadata"):
            crop = context.metadata.get("crop")
            if crop:
                search_category = "crop_guide"

        cache_key = self.get_query_cache_key(query, limit, search_category)
        cached = self.check_query_cache(cache_key)
        if cached is not None:
            return cached

        # 1. Search candidate pool
        candidates = await self.hybrid_search.search(query, limit=limit * 2, category=search_category)

        # 2. Filter invalid/deprecated candidates
        valid_candidates = []
        for cand in candidates:
            if self.freshness_scorer.is_valid(cand.get("metadata", {})):
                valid_candidates.append(cand)

        # 3. Rerank candidates
        reranked = self.rerank_engine.rerank(query, valid_candidates)

        # 4. Generate and attach citations
        final_results = []
        for doc in reranked[:limit]:
            citation_info = self.citation_builder.build_citations(doc)
            doc_copy = doc.copy()
            doc_copy["citation"] = citation_info["citation"]
            doc_copy["explanation"] = citation_info["explanation"]
            doc_copy["citation_metadata"] = citation_info
            final_results.append(doc_copy)

        self.set_query_cache(cache_key, final_results)
        return final_results

    async def search(
        self,
        query: str,
        limit: int = 5,
        context: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Adapter routing directly to retrieve.
        """
        return await self.retrieve(query, limit=limit, context=context)

    def rerank(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Direct access to multi-criteria reranking pipeline.
        """
        return cast(List[Dict[str, Any]], self.rerank_engine.rerank(query, documents))

    def build_citations(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Direct access to citation generation.
        """
        return cast(Dict[str, Any], self.citation_builder.build_citations(document))

    def score_freshness(self, document: Dict[str, Any]) -> float:
        """
        Direct access to freshness scoring.
        """
        return float(self.freshness_scorer.calculate_freshness_score(document.get("metadata", {})))
