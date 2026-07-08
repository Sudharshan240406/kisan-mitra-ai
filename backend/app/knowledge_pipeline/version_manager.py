import difflib
import logging
import time
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .document_parser import ParsedDocument

logger = logging.getLogger("kisan_mitra_ai.knowledge_pipeline.version_manager")

class DocumentHistoryRecord(BaseModel):
    """
    Registry item storing version metrics.
    """
    doc_id: str
    version: str
    title: str
    checksum: str
    status: str = "draft"  # draft | published | archived
    updated_at: float = Field(default_factory=time.time)
    document: ParsedDocument

class VersionManager:
    """
    Maintains historic logs of all published files, enabling version diffing and rollback triggers.
    """
    def __init__(self) -> None:
        # doc_id -> list of historic records (newest first)
        self.history: Dict[str, List[DocumentHistoryRecord]] = {}

    def register_version(self, doc: ParsedDocument, checksum: str, status: str = "draft") -> DocumentHistoryRecord:
        """
        Creates a new version entry inside the document history log.
        """
        record = DocumentHistoryRecord(
            doc_id=doc.doc_id,
            version=doc.version,
            title=doc.title,
            checksum=checksum,
            status=status,
            document=doc
        )
        if doc.doc_id not in self.history:
            self.history[doc.doc_id] = []

        # Deactivate older records if this one is published
        if status == "published":
            for r in self.history[doc.doc_id]:
                if r.status == "published":
                    r.status = "archived"

        self.history[doc.doc_id].insert(0, record)
        logger.info(f"[VersionManager] Registered version {doc.version} for document {doc.doc_id} as status '{status}'")
        return record

    def get_latest(self, doc_id: str) -> Optional[DocumentHistoryRecord]:
        """
        Retrieves the latest version record.
        """
        records = self.history.get(doc_id)
        return records[0] if records else None

    def get_active_published(self, doc_id: str) -> Optional[DocumentHistoryRecord]:
        """
        Retrieves the currently active 'published' document record.
        """
        records = self.history.get(doc_id)
        if records:
            for r in records:
                if r.status == "published":
                    return r
        return None

    def rollback_to_version(self, doc_id: str, target_version: str) -> DocumentHistoryRecord:
        """
        Rolls back the active document representation to a target version string.
        """
        records = self.history.get(doc_id)
        if not records:
            raise KeyError(f"No history found for document '{doc_id}'")

        target_record = None
        for r in records:
            if r.version == target_version:
                target_record = r
                break

        if not target_record:
            raise KeyError(f"Version '{target_version}' not found for document '{doc_id}'")

        # Inactivate current published version
        for r in records:
            if r.status == "published":
                r.status = "archived"

        # Mark target as active published
        target_record.status = "published"
        target_record.updated_at = time.time()
        logger.info(f"[VersionManager] Rolled back document '{doc_id}' to version '{target_version}'")
        return target_record

    def generate_diff(self, doc_id: str, v1: str, v2: str) -> str:
        """
        Computes a line-by-line diff between two document versions.
        """
        records = self.history.get(doc_id)
        if not records:
            raise KeyError(f"No history found for document '{doc_id}'")

        doc1 = next((r.document for r in records if r.version == v1), None)
        doc2 = next((r.document for r in records if r.version == v2), None)

        if not doc1 or not doc2:
            raise KeyError(f"Failed to find target versions {v1} and/or {v2} for diffing")

        # Synthesize lines for diff comparison
        def get_lines(doc: ParsedDocument) -> List[str]:
            lines = [f"Title: {doc.title}", f"Language: {doc.language}", f"Version: {doc.version}"]
            for sec in doc.sections:
                lines.append(f"Heading: {sec.heading}")
                lines.extend(sec.content.splitlines())
            return lines

        diff = difflib.unified_diff(
            get_lines(doc1),
            get_lines(doc2),
            fromfile=f"{doc_id}_v{v1}",
            tofile=f"{doc_id}_v{v2}"
        )
        return "\n".join(diff)
