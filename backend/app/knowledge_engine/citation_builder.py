import datetime
import logging
from typing import Any, Dict

logger = logging.getLogger("kisan_mitra_ai.knowledge_engine.citation_builder")

class CitationBuilder:
    """
    Constructs citation schemas and explainability metadata for knowledge retrieval items.
    """
    def build_citations(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a document candidate and returns citation mappings along with explainability rationale.
        """
        metadata = doc.get("metadata", {})

        # Resolve fields (support both flat structure and nested metadata structure)
        doc_id = doc.get("document_id") or metadata.get("document_id") or "doc-unknown"
        title = doc.get("title") or metadata.get("title") or "Reference Document"
        section = doc.get("section") or metadata.get("section") or "General Section"
        confidence = doc.get("confidence") or metadata.get("confidence") or doc.get("score", 0.5)
        source_type = doc.get("category") or metadata.get("source_type") or "reference"
        authority = metadata.get("authority", "authoritative agricultural archive")

        # Format datetime for explanation
        last_updated = metadata.get("last_updated")
        if last_updated:
            try:
                date_str = datetime.datetime.fromtimestamp(last_updated, tz=datetime.timezone.utc).strftime("%Y-%m-%d")
            except Exception:
                date_str = "recently"
        else:
            date_str = "recently"

        # Build human-readable formatted citation string
        formatted_citation = f"Source: {title} (ID: {doc_id}), Section: {section} [Confidence: {confidence:.2f}]"

        # Build explainability statement
        explanation = (
            f"This reference from '{title}' (Section: '{section}') is included because "
            f"it matches the semantic intent of your query with an overall confidence rating of {confidence * 100:.1f}%. "
            f"It is sourced from the official authority '{authority}', updated {date_str}, and version '{metadata.get('version', '1.0.0')}'."
        )

        return {
            "document_id": doc_id,
            "title": title,
            "section": section,
            "confidence": round(confidence, 4),
            "source_type": source_type,
            "citation": formatted_citation,
            "explanation": explanation
        }
