import hashlib
import logging
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from .document_parser import ParsedDocument

logger = logging.getLogger("kisan_mitra_ai.knowledge_pipeline.validation")

class ValidationReport(BaseModel):
    """
    Validation results describing checks status.
    """
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    hash_checksum: str

class ValidationEngine:
    """
    Ensures strict validation rules are met before publishing document packages.
    """
    def __init__(self, version_manager: Any = None) -> None:
        self.version_manager = version_manager
        # Store active hashes in memory to prevent duplicate ingestions
        self.indexed_hashes: Dict[str, str] = {}  # hash -> doc_id

    def calculate_checksum(self, doc: ParsedDocument) -> str:
        """
        Calculates SHA256 checksum from document contents.
        """
        hasher = hashlib.sha256()
        # Hash title and all section contents
        hasher.update(doc.title.encode("utf-8"))
        for sec in doc.sections:
            hasher.update(sec.heading.encode("utf-8"))
            hasher.update(sec.content.encode("utf-8"))
        return hasher.hexdigest()

    def validate_document(self, doc: ParsedDocument) -> ValidationReport:  # noqa: PLR0912
        errors = []
        warnings = []

        # 1. Broken / Missing Metadata
        if not doc.doc_id or doc.doc_id.strip() == "":
            errors.append("Missing document unique identifier (doc_id)")
        if not doc.title or doc.title.strip() == "":
            errors.append("Document title is empty or missing")
        if not doc.version or doc.version.strip() == "":
            errors.append("Document version is empty or missing")

        # 2. Incomplete Ingestion
        if not doc.sections:
            errors.append("Document contains no valid headings or content sections")
        else:
            for i, sec in enumerate(doc.sections):
                if not sec.heading or sec.heading.strip() == "":
                    errors.append(f"Section {i} has a missing heading")
                if not sec.content or sec.content.strip() == "":
                    warnings.append(f"Section '{sec.heading}' content is empty")

        # Compute checksum
        checksum = self.calculate_checksum(doc)

        # 3. Duplicate Document Checks
        if checksum in self.indexed_hashes:
            dup_id = self.indexed_hashes[checksum]
            if dup_id != doc.doc_id:
                errors.append(f"Duplicate document content detected matching existing document '{dup_id}'")
            else:
                warnings.append(f"Document '{doc.doc_id}' content matches previously indexed version")

        # 4. Outdated Version Checks
        if self.version_manager:
            latest = self.version_manager.get_latest(doc.doc_id)
            if latest:
                # Simple version tuple checking e.g. "1.1.0" > "1.0.0"
                if self._compare_versions(doc.version, latest.version) <= 0:
                    errors.append(f"Outdated document version '{doc.version}' submitted. Latest registered version is '{latest.version}'")

        # Update in-memory hash index if valid
        is_valid = len(errors) == 0
        if is_valid:
            self.indexed_hashes[checksum] = doc.doc_id

        return ValidationReport(
            valid=is_valid,
            errors=errors,
            warnings=warnings,
            hash_checksum=checksum
        )

    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        Compares version strings. Returns:
        - 1 if v1 > v2
        - -1 if v1 < v2
        - 0 if v1 == v2
        """
        def parse_v(v: str) -> List[int]:
            try:
                # Strip letters/characters, split dot notation
                return [int(x) for x in re.sub(r"[^\d.]", "", v).split(".")]
            except Exception:
                return [0]

        import re
        parts1 = parse_v(v1)
        parts2 = parse_v(v2)

        # Pad with zeros
        max_len = max(len(parts1), len(parts2))
        parts1.extend([0] * (max_len - len(parts1)))
        parts2.extend([0] * (max_len - len(parts2)))

        for p1, p2 in zip(parts1, parts2, strict=False):
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0
