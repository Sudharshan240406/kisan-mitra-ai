import re
from typing import Any, Dict, List


class VectorMemoryIndex:
    """
    Lightweight, zero-dependency semantic vector memory index.
    Uses TF-IDF overlap to rank documents based on query similarity.
    """
    def __init__(self) -> None:
        self.documents: List[Dict[str, Any]] = []

    def _tokenize(self, text: str) -> List[str]:
        # Simple word tokenization and normalization
        words = re.findall(r"\w+", text.lower())
        return [w for w in words if len(w) > 2]

    def add_document(self, text: str, metadata: Dict[str, Any]) -> None:
        self.documents.append({
            "text": text,
            "metadata": metadata,
            "tokens": self._tokenize(text)
        })

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        query_tokens = set(self._tokenize(query))
        if not query_tokens or not self.documents:
            return self.documents[:k]

        scored_docs = []
        # Calculate term overlap metrics
        for doc in self.documents:
            doc_tokens = doc["tokens"]
            intersection = query_tokens.intersection(doc_tokens)

            # Simple Jaccard similarity coefficient as semantic distance
            union_len = len(query_tokens.union(doc_tokens))
            score = len(intersection) / union_len if union_len > 0 else 0.0

            scored_docs.append((score, doc))

        # Sort descending by score
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, doc in scored_docs[:k]:
            results.append({
                "text": doc["text"],
                "metadata": doc["metadata"],
                "similarity": score
            })

        return results

    def clear(self) -> None:
        self.documents = []
