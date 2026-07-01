import logging
import time
from typing import Any, Optional

from app.core.context import AgentContext
from app.knowledge.core import KnowledgePlatform

logger = logging.getLogger("kisan_mitra_ai.knowledge.retrieval")


class KnowledgeRanker:
    """
    Ranks hybrid search results by weight, freshness, source authority, and query match scores.
    """
    def __init__(self) -> None:
        # Define source authority weights
        self.source_weights = {
            "government_schemes_db": 1.0,
            "crop_agronomy_manuals": 0.9,
            "soil_chemistry_manuals": 0.85,
            "crop_pathology_manuals": 0.9,
            "weather_advisories_db": 0.8,
            "market_prices_db": 0.75,
            "faiss": 0.65,
            "chroma": 0.65,
            "qdrant": 0.65,
            "pinecone": 0.65
        }

    def rank(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Ranks candidates and updates their confidence scores.
        """
        now = time.time()
        for cand in candidates:
            base_score = cand.get("score", 0.5)
            source = cand.get("source", "unknown")
            source_weight = self.source_weights.get(source, 0.5)

            # Age decay penalty (e.g. fresh data gets boost)
            last_updated = cand.get("metadata", {}).get("last_updated", now)
            age_days = (now - last_updated) / (24 * 3600)
            age_factor = max(0.8, 1.0 - (age_days / 365.0)) # cap at 20% decay per year

            # Authoritative source boost
            is_authoritative = cand.get("metadata", {}).get("authoritative", True)
            auth_boost = 1.1 if is_authoritative else 0.9

            final_score = base_score * source_weight * age_factor * auth_boost
            cand["confidence"] = round(min(final_score, 1.0), 3)

        # Sort in descending order of confidence score
        candidates.sort(key=lambda x: x["confidence"], reverse=True)
        return candidates


class KnowledgeRetrievalEngine:
    """
    Coordinates semantic search, vector databases, structured directories, and graph lookups.
    """
    def __init__(self, platform: KnowledgePlatform) -> None:
        self.platform = platform
        self.ranker = KnowledgeRanker()

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        context: Optional[AgentContext] = None
    ) -> list[dict[str, Any]]:
        """
        Performs hybrid retrieval across all registered providers, aggregates results, and ranks them.
        """
        candidates: list[dict[str, Any]] = []
        providers = self.platform.manager.registry.list_providers()

        # Query all registered knowledge providers in parallel
        for provider_key in providers:
            try:
                results = await self.platform.manager.query_provider(
                    provider_key=provider_key,
                    query=query,
                    limit=limit,
                    context=context
                )
                for res in results:
                    candidates.append(res)
            except Exception as e:
                logger.error(f"RetrievalEngine: Failed to query provider '{provider_key}': {e}")

        # Apply hybrid ranking
        ranked_results = self.ranker.rank(candidates)

        # Remove duplicate results
        unique_results = self._deduplicate(ranked_results)

        # Append citations to results
        for idx, item in enumerate(unique_results):
            source_name = item.get("source", "Reference Library")
            title = item.get("title", f"Document Record {idx+1}")
            doc_id = item.get("id", "doc-ref")
            item["citation"] = f"Citation [{idx+1}]: Source '{source_name}', Record '{title}' (ID: {doc_id})"

        return unique_results[:limit]

    def _deduplicate(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Removes identical entries or highly similar results.
        """
        seen_ids = set()
        seen_contents = set()
        deduped = []
        for cand in candidates:
            cid = cand.get("id")
            content = cand.get("content", "").strip().lower()

            if cid and cid in seen_ids:
                continue
            if content in seen_contents:
                continue

            if cid:
                seen_ids.add(cid)
            if content:
                seen_contents.add(content)

            deduped.append(cand)
        return deduped
