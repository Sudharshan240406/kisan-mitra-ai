import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kisan_mitra_ai.knowledge_engine.chunk_manager")

class ChunkManager:
    """
    Splits documents into clean semantic chunks with adaptive sizes, overlap,
    metadata injection, and caching of computed embeddings.
    """
    def __init__(self, default_chunk_size: int = 500, default_overlap: int = 50) -> None:
        self.default_chunk_size = default_chunk_size
        self.default_overlap = default_overlap
        self._embedding_cache: Dict[str, List[float]] = {}

    def get_embedding_from_cache(self, text: str) -> Optional[List[float]]:
        return self._embedding_cache.get(text)

    def cache_embedding(self, text: str, embedding: List[float]) -> None:
        self._embedding_cache[text] = embedding

    def invalidate_embedding(self, text: str) -> None:
        if text in self._embedding_cache:
            del self._embedding_cache[text]

    def clear_embedding_cache(self) -> None:
        self._embedding_cache.clear()

    def chunk_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Splits a text document into chunks adaptively based on paragraph and sentence boundaries.
        Returns a list of chunk dictionaries containing 'content' and 'metadata'.
        """
        size = chunk_size or self.default_chunk_size
        over = overlap or self.default_overlap
        meta = metadata or {}

        if not text.strip():
            return []

        # Split text into paragraphs first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        # Adaptive chunking logic
        chunks: List[Dict[str, Any]] = []
        current_chunk_parts: List[str] = []
        current_length = 0

        for paragraph in paragraphs:
            para_len = len(paragraph)

            # If paragraph itself is too large, split it into sentences
            if para_len > size:
                # If we have accumulated parts, flush them
                if current_chunk_parts:
                    chunks.append(self._create_chunk_dict(current_chunk_parts, meta))
                    # Reset with overlap
                    current_chunk_parts = self._get_overlap_parts(current_chunk_parts, over)
                    current_length = sum(len(p) for p in current_chunk_parts)

                sentences = [s.strip() + "." for s in paragraph.split(". ") if s.strip()]
                for sentence in sentences:
                    # Clean punctuation helper to prevent double dots
                    clean_sentence = sentence[:-1] if sentence.endswith("..") else sentence
                    sent_len = len(clean_sentence)
                    if current_length + sent_len > size and current_chunk_parts:
                        chunks.append(self._create_chunk_dict(current_chunk_parts, meta))
                        current_chunk_parts = self._get_overlap_parts(current_chunk_parts, over)
                        current_length = sum(len(p) for p in current_chunk_parts)

                    current_chunk_parts.append(clean_sentence)
                    current_length += sent_len
            else:
                if current_length + para_len > size and current_chunk_parts:
                    chunks.append(self._create_chunk_dict(current_chunk_parts, meta))
                    current_chunk_parts = self._get_overlap_parts(current_chunk_parts, over)
                    current_length = sum(len(p) for p in current_chunk_parts)

                current_chunk_parts.append(paragraph)
                current_length += para_len

        if current_chunk_parts:
            chunks.append(self._create_chunk_dict(current_chunk_parts, meta))

        # Add index numbers to chunk metadata
        for idx, chunk in enumerate(chunks):
            chunk["metadata"] = {
                **meta,
                "chunk_index": idx,
                "total_chunks": len(chunks)
            }

        return chunks

    def _create_chunk_dict(self, parts: List[str], base_metadata: Dict[str, Any]) -> Dict[str, Any]:
        content = " ".join(parts)
        return {
            "content": content,
            "metadata": base_metadata.copy()
        }

    def _get_overlap_parts(self, parts: List[str], overlap_size: int) -> List[str]:
        """Keep the last few parts that fit within the overlap size."""
        overlap_parts: List[str] = []
        current_len = 0
        for part in reversed(parts):
            if current_len + len(part) <= overlap_size:
                overlap_parts.insert(0, part)
                current_len += len(part)
            else:
                break
        # If overlap parts is empty but we have parts, keep at least the last part
        if not overlap_parts and parts:
            overlap_parts.append(parts[-1])
        return overlap_parts
