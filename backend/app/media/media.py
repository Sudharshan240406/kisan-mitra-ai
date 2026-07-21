import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

import httpx
from app.core.config import settings
from app.utils.id import generate_uuid
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.media")


class MediaType(str, Enum):
    """Supported media input types."""
    VOICE = "voice"
    IMAGE = "image"
    DOCUMENT = "document"
    SENSOR = "sensor"
    DRONE_IMAGE = "drone_image"
    VIDEO = "video"


class MediaStatus(str, Enum):
    """Media provider status codes."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


class MediaMetadata(BaseModel):
    """
    Standard metadata describing an ingested media input.
    """
    file_size_bytes: int = Field(..., description="File size in bytes.")
    format: str = Field(..., description="Media file format extension (e.g. mp3, wav, png, pdf).")
    duration_seconds: Optional[float] = Field(default=None, description="Playback duration if audio/video.")
    mime_type: Optional[str] = Field(default=None, description="Content MIME type descriptor.")
    additional_metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible metadata tags.")


class MediaInput(BaseModel):
    """
    Universal input structure representing raw media file ingestion.
    """
    media_id: str = Field(default_factory=generate_uuid, description="Unique media tracker ID.")
    media_type: MediaType = Field(..., description="Ingested media classification.")
    filename: str = Field(..., description="Source filename.")
    content: bytes = Field(..., description="Binary media payload bytes.")
    metadata: MediaMetadata = Field(..., description="Associated file descriptor metadata.")


class MediaResult(BaseModel):
    """
    Standard output payload returned by the Media Intelligence layer.
    """
    media_id: str = Field(..., description="Reference to source media input ID.")
    success: bool = Field(..., description="Indicates if processing was successful.")
    extracted_text: Optional[str] = Field(default=None, description="Extracted transcribed/OCR text output.")
    confidence: float = Field(default=1.0, description="Processing classification confidence score.")
    anomalies: list[str] = Field(default_factory=list, description="List of agricultural anomalies detected.")
    classification_tags: list[str] = Field(default_factory=list, description="Target categorization tags.")
    warnings: list[str] = Field(default_factory=list, description="Operational flags or content warning indicators.")
    severity: Optional[str] = Field(default=None, description="Optional severity descriptor for CV/OCR findings.")
    suggested_actions: list[str] = Field(default_factory=list, description="Provider-suggested next actions.")
    extracted_entities: dict[str, Any] = Field(default_factory=dict, description="Structured entities extracted from media.")
    evidence_payload: list[dict[str, Any]] = Field(default_factory=list, description="Optional structured evidence emitted by the media provider.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible result metrics.")


class IMediaProvider(ABC):
    """
    Abstract interface defining capabilities that all media providers must implement.
    """
    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @property
    @abstractmethod
    def capabilities(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def status(self) -> MediaStatus:
        pass

    @property
    @abstractmethod
    def latency_ms(self) -> float:
        pass

    @property
    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        pass

    @abstractmethod
    async def process(self, media_input: MediaInput) -> MediaResult:
        """Processes the media input and returns the structured extraction result."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Performs dynamic health verification of the provider."""
        pass


class BaseMediaProvider(IMediaProvider):
    """
    Base class implementing shared attributes and boilerplate code for media providers.
    """
    def __init__(
        self,
        provider_id: str,
        version: str = "1.0.0",
        capabilities: Optional[list[str]] = None
    ) -> None:
        self._id = provider_id
        self._version = version
        self._capabilities = capabilities or []
        self._status = MediaStatus.ACTIVE
        self._latency_ms = 0.0
        self._metadata: dict[str, Any] = {}

    @property
    def id(self) -> str:
        return self._id

    @property
    def version(self) -> str:
        return self._version

    @property
    def capabilities(self) -> list[str]:
        return self._capabilities

    @property
    def status(self) -> MediaStatus:
        return self._status

    @status.setter
    def status(self, val: MediaStatus) -> None:
        self._status = val

    @property
    def latency_ms(self) -> float:
        return self._latency_ms

    @latency_ms.setter
    def latency_ms(self, val: float) -> None:
        self._latency_ms = val

    @property
    def metadata(self) -> dict[str, Any]:
        return self._metadata

    async def health_check(self) -> bool:
        return self._status == MediaStatus.ACTIVE


class VoiceProvider(BaseMediaProvider):
    """Voice Speech-to-Text processor."""
    async def process(self, media_input: MediaInput) -> MediaResult:
        start_time = time.perf_counter()

        # Simulates STT by converting payload content bytes to text if clean utf-8,
        # otherwise returning a default simulated voice request query.
        text = "What is the recommended fertilizer for wheat crops in Punjab?"
        try:
            decoded = media_input.content.decode("utf-8", errors="ignore").strip()
            if len(decoded) > 5:
                text = decoded
        except Exception:
            pass

        duration = round((time.perf_counter() - start_time) * 1000, 4)
        self.latency_ms = duration

        return MediaResult(
            media_id=media_input.media_id,
            success=True,
            extracted_text=text,
            confidence=0.98,
            classification_tags=["voice_query", "fertilizer"],
            suggested_actions=["Confirm the crop and location before applying fertilizer."],
            extracted_entities={"crop": "wheat", "location": "Punjab"},
            evidence_payload=[{
                "id": f"EV-{media_input.media_id[:8]}",
                "source": self.id,
                "agent": "Voice",
                "confidence": 0.98,
                "reasoning": text,
                "metadata": {
                    "intent": "voice_query",
                    "suggested_actions": ["Confirm the crop and location before applying fertilizer."],
                    "crop": "wheat",
                    "location": "Punjab",
                },
            }],
            metadata={"transcription_engine": "mock_whisper", "processing_time_ms": duration, "provider_id": self.id}
        )


class ImageProvider(BaseMediaProvider):
    """Image Computer Vision and OCR processor."""
    async def process(self, media_input: MediaInput) -> MediaResult:
        start_time = time.perf_counter()

        # Simulates scan for yellow rust on wheat leaf image
        tags = ["leaf", "wheat"]
        anomalies = []
        text = "Scan label: Wheat Leaf"

        try:
            content_str = media_input.content.decode("utf-8", errors="ignore")
            if "rust" in content_str.lower() or "yellow" in content_str.lower():
                tags.append("rust")
                anomalies.append("Yellow Rust Disease detected")
                text = "Leaf contains yellow spot patches indicative of wheat rust."
        except Exception:
            pass

        # Real Google Vision OCR integration if configured
        api_key = settings.GOOGLE_VISION_API_KEY
        if api_key and media_input.content:
            try:
                import base64
                encoded_image = base64.b64encode(media_input.content).decode("utf-8")
                url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
                payload = {
                    "requests": [
                        {
                            "image": {"content": encoded_image},
                            "features": [{"type": "TEXT_DETECTION"}]
                        }
                    ]
                }
                async with httpx.AsyncClient(timeout=8.0) as client:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        responses_data = response.json().get("responses", [])
                        if responses_data:
                            full_text = responses_data[0].get("fullTextAnnotation", {}).get("text", "")
                            if full_text:
                                text = f"OCR Extracted text:\n{full_text}"
                                if "rust" in full_text.lower() or "yellow" in full_text.lower():
                                    tags.append("rust")
                                    anomalies.append("Yellow Rust Disease detected")
            except Exception as e:
                logger.warning(f"[ImageProvider] Google Vision OCR failed: {e}")

        duration = round((time.perf_counter() - start_time) * 1000, 4)
        self.latency_ms = duration

        return MediaResult(
            media_id=media_input.media_id,
            success=True,
            extracted_text=text,
            confidence=0.92,
            anomalies=anomalies,
            classification_tags=tags,
            severity="medium" if anomalies else "low",
            suggested_actions=["Inspect nearby leaves for similar lesions.", "Consult disease management guidance before spraying."],
            extracted_entities={"crop": "wheat", "possible_disease": "yellow_rust" if anomalies else None},
            evidence_payload=[{
                "id": f"EV-{media_input.media_id[:8]}",
                "source": self.id,
                "agent": "Vision",
                "confidence": 0.92,
                "reasoning": text,
                "metadata": {
                    "crop": "wheat",
                    "severity": "medium" if anomalies else "low",
                    "suggested_actions": ["Inspect nearby leaves for similar lesions.", "Consult disease management guidance before spraying."],
                    "classification_tags": tags,
                },
                "symptoms": anomalies or ["No visible disease anomalies detected."],
                "pathogen": "yellow_rust" if anomalies else None,
            }],
            metadata={"cv_engine": "mock_resnet", "processing_time_ms": duration, "provider_id": self.id}
        )


class DocumentProvider(BaseMediaProvider):
    """Document parser."""
    async def process(self, media_input: MediaInput) -> MediaResult:
        start_time = time.perf_counter()

        text = "Document summary details: Farmer record registry details."
        try:
            content_str = media_input.content.decode("utf-8", errors="ignore")
            if len(content_str) > 10:
                text = content_str
        except Exception:
            pass

        duration = round((time.perf_counter() - start_time) * 1000, 4)
        self.latency_ms = duration

        return MediaResult(
            media_id=media_input.media_id,
            success=True,
            extracted_text=text,
            confidence=0.95,
            classification_tags=["document_report"],
            suggested_actions=["Review extracted scheme or soil-card details with the farmer."],
            extracted_entities={"document_type": "government_document" if "scheme" in text.lower() else "report"},
            evidence_payload=[{
                "id": f"EV-{media_input.media_id[:8]}",
                "source": self.id,
                "agent": "OCR",
                "confidence": 0.95,
                "reasoning": text,
                "metadata": {
                    "document_type": "government_document" if "scheme" in text.lower() else "report",
                    "suggested_actions": ["Review extracted scheme or soil-card details with the farmer."],
                },
                "citation": media_input.filename,
                "document_title": media_input.filename,
            }],
            metadata={"parser_engine": "mock_pdfminer", "processing_time_ms": duration, "provider_id": self.id}
        )


class SensorProvider(BaseMediaProvider):
    """Agricultural IoT sensor parser."""
    async def process(self, media_input: MediaInput) -> MediaResult:
        start_time = time.perf_counter()

        anomalies = []
        try:
            content_str = media_input.content.decode("utf-8", errors="ignore").lower()
            if "moisture:10" in content_str or "dry" in content_str:
                anomalies.append("Soil Moisture critical: Low (10%)")
        except Exception:
            pass

        duration = round((time.perf_counter() - start_time) * 1000, 4)
        self.latency_ms = duration

        return MediaResult(
            media_id=media_input.media_id,
            success=True,
            extracted_text=f"Sensor log read: {len(media_input.content)} bytes",
            confidence=1.0,
            anomalies=anomalies,
            classification_tags=["iot_sensor_data"],
            suggested_actions=["Cross-check soil moisture against irrigation schedule."],
            metadata={"sensor_type": "moisture_log", "processing_time_ms": duration, "provider_id": self.id}
        )


class DroneImageProvider(BaseMediaProvider):
    """Drone image spatial crop analyst."""
    async def process(self, media_input: MediaInput) -> MediaResult:
        start_time = time.perf_counter()

        duration = round((time.perf_counter() - start_time) * 1000, 4)
        self.latency_ms = duration

        return MediaResult(
            media_id=media_input.media_id,
            success=True,
            extracted_text="Drone spatial grid scan: NDVI index shows normal crop density.",
            confidence=0.88,
            classification_tags=["drone_gis_ndvi"],
            suggested_actions=["Review field zones with lower NDVI if future scans decline."],
            metadata={"spatial_engine": "mock_gdal", "processing_time_ms": duration, "provider_id": self.id}
        )


class VideoProvider(BaseMediaProvider):
    """Video stream analyst."""
    async def process(self, media_input: MediaInput) -> MediaResult:
        start_time = time.perf_counter()

        duration = round((time.perf_counter() - start_time) * 1000, 4)
        self.latency_ms = duration

        return MediaResult(
            media_id=media_input.media_id,
            success=True,
            extracted_text="Video keyframes scanned: normal crop movement, no severe storm activity detected.",
            confidence=0.85,
            classification_tags=["video_feed_scan"],
            suggested_actions=["Continue monitoring field conditions for movement or storm damage."],
            metadata={"video_engine": "mock_ffmpeg_cv", "processing_time_ms": duration, "provider_id": self.id}
        )


class MediaProviderRegistry:
    """
    Registry supervising loading, versioning, health, and registry tracking of media providers.
    """
    def __init__(self, event_bus: Optional[Any] = None, governance_engine: Optional[Any] = None) -> None:
        self._providers: dict[str, IMediaProvider] = {}
        self._event_bus = event_bus
        self._governance_engine = governance_engine

    def register(self, provider: IMediaProvider) -> None:
        """Registers a media provider into the MIP."""
        self._providers[provider.id] = provider
        logger.info(f"Registered Media Provider '{provider.id}' v{provider.version}.")

        # Auto-register with Governance Engine if present
        if self._governance_engine:
            try:
                self._governance_engine.register_artifact(
                    artifact_type="media_provider",
                    artifact_id=provider.id,
                    version=provider.version,
                    status=provider.status.value
                )
            except Exception as e:
                logger.error(f"Failed to register provider '{provider.id}' in governance ledger: {e}")

    def deregister(self, provider_id: str) -> None:
        """Deregisters a media provider."""
        if provider_id in self._providers:
            del self._providers[provider_id]
            logger.info(f"Deregistered Media Provider '{provider_id}'.")

    def discover(self, provider_id: str) -> Optional[IMediaProvider]:
        """Looks up a media provider by ID."""
        return self._providers.get(provider_id)

    def discover_by_type(self, media_type: MediaType) -> list[IMediaProvider]:
        """Discovers media providers matching capabilities for a specific media type."""
        # Simple lookup strategy: matches capabilities containing media type
        matches = []
        for provider in self._providers.values():
            for cap in provider.capabilities:
                # E.g. if capability is "speech_to_text" and media type is voice, it matches
                if media_type == MediaType.VOICE and ("speech" in cap or "voice" in cap):
                    matches.append(provider)
                    break
                elif media_type == MediaType.IMAGE and ("ocr" in cap or "image" in cap or "disease" in cap):
                    matches.append(provider)
                    break
                elif media_type == MediaType.DOCUMENT and ("doc" in cap or "pdf" in cap or "parsing" in cap):
                    matches.append(provider)
                    break
                elif media_type == MediaType.SENSOR and ("sensor" in cap or "anomaly" in cap or "moisture" in cap):
                    matches.append(provider)
                    break
                elif media_type == MediaType.DRONE_IMAGE and ("drone" in cap or "ndvi" in cap or "gis" in cap):
                    matches.append(provider)
                    break
                elif media_type == MediaType.VIDEO and ("video" in cap or "ffmpeg" in cap or "frame" in cap):
                    matches.append(provider)
                    break
        return matches

    def list_providers(self) -> list[IMediaProvider]:
        """Lists all registered media providers."""
        return list(self._providers.values())

    def validate_dependencies(self, provider_id: str) -> bool:
        """Validates that a media provider has its configured properties."""
        provider = self.discover(provider_id)
        if not provider:
            return False
        # General validations: ensure id, version, status, capabilities are formatted
        if not provider.id or not provider.version or not provider.status:
            return False
        return True

    def load_from_config(self, configs: list[dict[str, Any]]) -> None:
        """Dynamically instantiates and registers mock providers from a configuration array."""
        for cfg in configs:
            try:
                pid = cfg.get("provider_id")
                mtype_str = cfg.get("media_type")
                version = cfg.get("version", "1.0.0")
                caps = cfg.get("capabilities", [])

                if not pid or not mtype_str:
                    continue

                mtype = MediaType(mtype_str)
                provider: IMediaProvider

                if mtype == MediaType.VOICE:
                    provider = VoiceProvider(pid, version, caps)
                elif mtype == MediaType.IMAGE:
                    provider = ImageProvider(pid, version, caps)
                elif mtype == MediaType.DOCUMENT:
                    provider = DocumentProvider(pid, version, caps)
                elif mtype == MediaType.SENSOR:
                    provider = SensorProvider(pid, version, caps)
                elif mtype == MediaType.DRONE_IMAGE:
                    provider = DroneImageProvider(pid, version, caps)
                elif mtype == MediaType.VIDEO:
                    provider = VideoProvider(pid, version, caps)
                else:
                    provider = BaseMediaProvider(pid, version, caps)

                self.register(provider)
            except Exception as e:
                logger.error(f"Failed to load media provider from configuration {cfg}: {e}")

    async def health_check(self) -> dict[str, Any]:
        """Queries health check across all registered providers."""
        report: dict[str, Any] = {}
        for pid, provider in self._providers.items():
            try:
                is_healthy = await provider.health_check()
                report[pid] = {
                    "version": provider.version,
                    "status": provider.status.value,
                    "healthy": is_healthy,
                    "latency_ms": provider.latency_ms
                }
            except Exception as e:
                report[pid] = {"healthy": False, "error": str(e)}
        return report
