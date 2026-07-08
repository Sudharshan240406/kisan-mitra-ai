import logging
import time
from typing import Any, Dict, List

from pydantic import BaseModel

from .document_parser import ParsedDocument

logger = logging.getLogger("kisan_mitra_ai.knowledge_pipeline.embedding")

class IngestionChunk(BaseModel):
    """
    Chunk partition schema with reference metadata.
    """
    chunk_id: str
    content: str
    metadata: Dict[str, Any]

class EmbeddingPipeline:
    """
    Splits text sections, computes embeddings, and indexes chunks.
    """
    def __init__(self, obs_mgr: Any = None) -> None:
        self.obs_mgr = obs_mgr

    def chunk_document(self, doc: ParsedDocument, chunk_words_limit: int = 300) -> List[IngestionChunk]:
        """
        Chunks section contents into smaller text segments.
        """
        chunks = []
        for sec in doc.sections:
            words = sec.content.split()
            # Split list into parts
            for i in range(0, len(words), chunk_words_limit):
                chunk_words = words[i:i + chunk_words_limit]
                chunk_text = " ".join(chunk_words)

                chunk_id = f"{doc.doc_id}_{sec.heading.lower().replace(' ', '_')}_{i//chunk_words_limit}"
                metadata = {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "section": sec.heading,
                    "version": doc.version,
                    "language": doc.language,
                    **doc.metadata
                }
                chunks.append(IngestionChunk(
                    chunk_id=chunk_id,
                    content=chunk_text,
                    metadata=metadata
                ))
        logger.info(f"[EmbeddingPipeline] Chunked document '{doc.doc_id}' into {len(chunks)} segments")
        return chunks

    async def generate_embeddings_and_index(self, chunks: List[IngestionChunk], vector_provider: Any) -> None:
        """
        Simulates vector generation and indexes chunks in the vector database.
        """
        start_time = time.time()
        logger.info(f"[EmbeddingPipeline] Indexing {len(chunks)} chunks using vector provider '{type(vector_provider).__name__}'")

        for chunk in chunks:
            # Call provider index_document API
            # FAISS/Chroma mock adapters accept content and metadata dictionary
            await vector_provider.index_document(chunk.content, {
                "chunk_id": chunk.chunk_id,
                **chunk.metadata
            })

        latency = (time.time() - start_time) * 1000.0
        if self.obs_mgr:
            self.obs_mgr.metrics_engine.record("embedding_latency", latency, {"chunks_count": len(chunks)})
        logger.info(f"[EmbeddingPipeline] Successfully indexed {len(chunks)} chunks in {latency:.2f}ms")
