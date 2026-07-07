import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kisan_mitra_ai.knowledge_engine.hybrid_search")

class HybridSearch:
    """
    Combines keyword (lexical) search and semantic (vector) search to return merged, ranked results.
    """
    def __init__(self, semantic_retriever: Any, alpha: float = 0.5) -> None:
        self.retriever = semantic_retriever
        self.alpha = alpha  # weight of semantic search vs keyword search
        self.stopwords = {
            "the", "a", "an", "in", "on", "at", "for", "with", "about", "against",
            "of", "by", "to", "is", "are", "and", "or", "but", "what", "how", "where", "who", "which"
        }

    def compute_keyword_score(self, query: str, content: str, title: str = "") -> float:
        """
        Computes a keyword overlap score based on query tokens appearing in content and title.
        """
        # Clean and tokenize query
        q_tokens = {
            t.strip("?,.!()-+=_@#$%^&*[]{}|\\/`~'\":;").lower()
            for t in query.split()
        }
        q_tokens = {t for t in q_tokens if t and t not in self.stopwords}
        if not q_tokens:
            return 0.0

        # Clean and tokenize content and title
        combined_text = f"{title} {content}".lower()

        matches = 0
        for token in q_tokens:
            if token in combined_text:
                matches += 1

        return matches / len(q_tokens)

    async def search(
        self,
        query: str,
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes semantic search, then calculates keyword score for candidates,
        and fuses them using weighted average score.
        """
        # To get a good candidate pool for keyword calculations, retrieve slightly more than limit
        candidate_limit = max(limit * 2, 10)
        semantic_results = await self.retriever.retrieve(
            query,
            limit=candidate_limit,
            category=category
        )

        hybrid_results: List[Dict[str, Any]] = []

        for sem_res in semantic_results:
            sem_score = sem_res.get("score", 0.0)
            content = sem_res.get("content", "")
            title = sem_res.get("title", "")

            # Compute lexical/keyword score
            key_score = self.compute_keyword_score(query, content, title)

            # Weighted fusion
            hybrid_score = (self.alpha * sem_score) + ((1.0 - self.alpha) * key_score)

            # Build merged entry
            res = sem_res.copy()
            res["semantic_score"] = round(sem_score, 4)
            res["keyword_score"] = round(key_score, 4)
            res["score"] = round(hybrid_score, 4) # overwrite the base score with hybrid score
            hybrid_results.append(res)

        # Sort combined list by hybrid score descending
        hybrid_results.sort(key=lambda x: x["score"], reverse=True)
        return hybrid_results[:limit]
