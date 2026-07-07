import logging
from typing import Any, Dict, List, Optional

from app.knowledge_engine.freshness import FreshnessScorer

logger = logging.getLogger("kisan_mitra_ai.knowledge_engine.reranker")

class Reranker:
    """
    Reranks retrieved knowledge documents based on multiple dimensions:
    semantic similarity, document quality, freshness, confidence, and authority.
    """
    def __init__(self, freshness_scorer: Optional[FreshnessScorer] = None) -> None:
        self.freshness_scorer = freshness_scorer or FreshnessScorer()
        # Default criteria weights
        self.default_weights = {
            "semantic": 0.4,
            "quality": 0.15,
            "freshness": 0.15,
            "confidence": 0.15,
            "authority": 0.15
        }
        self.official_keywords = [
            "government", "ministry", "central", "state", "council", "survey",
            "department", "authority", "official", "national", "cacp", "icar", "india"
        ]

    def get_authority_score(self, metadata: Dict[str, Any]) -> float:
        """
        Determines the authority score from metadata.
        Returns 1.0 if official, or a configured authority_score, or 0.5 default.
        """
        if metadata.get("authoritative") is True:
            return 1.0

        authority = metadata.get("authority", "").lower()
        if not authority:
            return 0.5

        if any(keyword in authority for keyword in self.official_keywords):
            return 1.0

        return float(metadata.get("authority_score", 0.6))

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        weights: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scores and ranks retrieved documents.
        """
        # Normalize weights
        w = weights or self.default_weights
        total_w = sum(w.values())
        norm_w = {k: val / total_w for k, val in w.items()}

        reranked_docs = []

        for doc in documents:
            metadata = doc.get("metadata", {})

            # 1. Semantic Similarity
            sim_score = doc.get("score", doc.get("semantic_score", 0.5))

            # 2. Document Quality
            qual_score = metadata.get("document_quality", 0.8)

            # 3. Freshness Score
            fresh_score = self.freshness_scorer.calculate_freshness_score(metadata)

            # 4. Confidence Score
            conf_score = metadata.get("confidence", 0.8)

            # 5. Authority Score
            auth_score = self.get_authority_score(metadata)

            # Composite weighted calculation
            composite_score = (
                norm_w["semantic"] * sim_score +
                norm_w["quality"] * qual_score +
                norm_w["freshness"] * fresh_score +
                norm_w["confidence"] * conf_score +
                norm_w["authority"] * auth_score
            )

            # Build detailed scoring entry for explainability
            doc_copy = doc.copy()
            doc_copy["scoring_breakdown"] = {
                "semantic": round(sim_score, 4),
                "quality": round(qual_score, 4),
                "freshness": round(fresh_score, 4),
                "confidence": round(conf_score, 4),
                "authority": round(auth_score, 4)
            }
            # Update candidate's search confidence and ranking score
            doc_copy["confidence"] = round(composite_score, 4)
            doc_copy["score"] = round(composite_score, 4)
            reranked_docs.append(doc_copy)

        # Sort by updated confidence score in descending order
        reranked_docs.sort(key=lambda x: x["confidence"], reverse=True)
        return reranked_docs
