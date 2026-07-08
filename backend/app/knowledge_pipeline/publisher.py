import logging
from typing import Any, List

from .document_parser import ParsedDocument
from .embedding_pipeline import IngestionChunk

logger = logging.getLogger("kisan_mitra_ai.knowledge_pipeline.publisher")

class Publisher:
    """
    Coordinates commits of validated content directly to active Vector Database providers.
    """
    def __init__(self, knowledge_platform: Any) -> None:
        self.knowledge_platform = knowledge_platform

    async def publish_document(self, doc: ParsedDocument, chunks: List[IngestionChunk]) -> None:
        """
        Pushes document chunks into FAISS and Chroma registries.
        """
        logger.info(f"[Publisher] Publishing document '{doc.doc_id}' v{doc.version}")

        # 1. Fetch registered vector stores from the Knowledge Platform registry
        if not self.knowledge_platform:
            logger.warning("[Publisher] KnowledgePlatform is not initialized. Bypassing publish.")
            return

        registry = self.knowledge_platform.manager.registry
        providers = registry.list_providers()

        target_providers = ["faiss", "chroma"]
        published_count = 0

        for prov_name in target_providers:
            if prov_name in providers:
                prov = registry.get(prov_name)
                # Write each chunk
                for chunk in chunks:
                    await prov.index_document(chunk.content, {
                        "chunk_id": chunk.chunk_id,
                        **chunk.metadata
                    })
                published_count += 1
                logger.info(f"[Publisher] Successfully published {len(chunks)} chunks to vector database: {prov_name}")

        # 2. Register version in the Knowledge platform's central version manager catalog if available
        # This keeps the core platform's catalog synchronized
        try:
            from app.knowledge.core import KnowledgeMetadata
            # Convert pipeline metadata to core Metadata
            meta = KnowledgeMetadata(
                id=doc.doc_id,
                source=doc.metadata.get("source", "Self-Updating Pipeline"),
                version=doc.version,
                authoritative=True,
                tags=doc.metadata.get("tags", [])
            )
            self.knowledge_platform.manager.version_manager.register_version(meta)
        except Exception as e:
            logger.warning(f"[Publisher] Failed to register version in core platform catalog: {e}")

        if published_count == 0:
            logger.warning("[Publisher] No active vector stores (FAISS or Chroma) found in registry. Published 0 stores.")
