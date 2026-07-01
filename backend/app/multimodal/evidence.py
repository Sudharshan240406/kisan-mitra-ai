from __future__ import annotations

from typing import Any

from app.media.media import MediaResult, MediaType
from app.multimodal.core import MediaContext
from app.schemas.evidence import BaseEvidence, DiseaseEvidence, KnowledgeEvidence, MemoryEvidence


class MultimodalEvidenceExtractor:
    """Converts multimodal extraction results into reasoning evidence."""

    def extract(
        self,
        media_result: MediaResult,
        context: MediaContext,
    ) -> list[BaseEvidence]:
        if media_result.evidence_payload:
            evidences: list[BaseEvidence] = []
            for payload in media_result.evidence_payload:
                evidences.append(self._materialize(payload))
            return evidences

        default_payload = {
            "id": f"MM-{media_result.media_id[:8]}",
            "source": media_result.metadata.get("provider_id", "multimodal"),
            "agent": self._agent_name(context.media_type),
            "confidence": media_result.confidence,
            "reasoning": media_result.extracted_text or "No extracted text available.",
            "metadata": {
                "classification_tags": media_result.classification_tags,
                "warnings": media_result.warnings,
                "suggested_actions": media_result.suggested_actions,
                "extracted_entities": media_result.extracted_entities,
                "severity": media_result.severity,
                **media_result.metadata,
            },
        }
        return [self._materialize(default_payload)]

    def _agent_name(self, media_type: MediaType) -> str:
        if media_type == MediaType.VOICE:
            return "Voice"
        if media_type == MediaType.IMAGE:
            return "Vision"
        if media_type == MediaType.DOCUMENT:
            return "OCR"
        return "Multimodal"

    def _materialize(self, payload: dict[str, Any]) -> BaseEvidence:
        agent = payload.get("agent", "Multimodal")
        if agent in {"Vision", "DiseaseAnalysis"}:
            return DiseaseEvidence.model_validate(payload)
        if agent in {"OCR", "Knowledge"}:
            return KnowledgeEvidence.model_validate(payload)
        if agent == "Voice":
            return MemoryEvidence.model_validate(payload)
        return BaseEvidence.model_validate(payload)
