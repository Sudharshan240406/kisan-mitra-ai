from __future__ import annotations

from typing import Any

from app.media.media import MediaInput, MediaType
from pydantic import BaseModel, Field


class ImageValidationReport(BaseModel):
    passed: bool = Field(..., description="True when the image is acceptable for downstream analysis.")
    blur_score: float = Field(default=1.0)
    brightness_score: float = Field(default=1.0)
    orientation_degrees: int = Field(default=0)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ImageValidationEngine:
    """Heuristic image validator using supplied metadata."""

    SUPPORTED_FORMATS = {"png", "jpg", "jpeg", "tiff", "tif"}

    def validate(self, media_input: MediaInput) -> ImageValidationReport:
        meta = media_input.metadata.additional_metadata
        blur_score = float(meta.get("blur_score", 0.9))
        brightness_score = float(meta.get("brightness_score", 0.8))
        orientation = int(meta.get("orientation_degrees", 0))

        warnings: list[str] = []
        errors: list[str] = []

        fmt = media_input.metadata.format.lower().replace(".", "")
        if fmt not in self.SUPPORTED_FORMATS:
            errors.append(f"Unsupported image format '{fmt}'.")
        if blur_score < 0.35:
            errors.append("Image is too blurry for reliable crop analysis.")
        elif blur_score < 0.55:
            warnings.append("Image blur detected; confidence may be reduced.")
        if brightness_score < 0.25:
            errors.append("Image is too dark for reliable analysis.")
        elif brightness_score < 0.45:
            warnings.append("Low brightness detected; consider a better-lit image.")
        if orientation not in {0, 90, 180, 270}:
            warnings.append("Image orientation is unusual; downstream OCR may degrade.")
        if media_input.metadata.file_size_bytes <= 0:
            errors.append("Image payload is empty.")

        return ImageValidationReport(
            passed=not errors,
            blur_score=blur_score,
            brightness_score=brightness_score,
            orientation_degrees=orientation,
            warnings=warnings,
            errors=errors,
        )


def supports_image_validation(media_type: MediaType) -> bool:
    return media_type in {MediaType.IMAGE, MediaType.DRONE_IMAGE}
