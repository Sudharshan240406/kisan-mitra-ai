import logging
from typing import Any

from app.core.config import settings
from app.core.integrations.base import IntegrationMetadata, IStorageAdapter

logger = logging.getLogger("kisan_mitra_ai.integrations.adapters.storage")


class LocalStorageAdapter(IStorageAdapter):
    """
    Local filesystem dictionary-backed storage adapter.
    """
    def __init__(self) -> None:
        self._metadata = IntegrationMetadata(
            id="local-storage",
            name="Local Filesystem Storage",
            version="1.0.0",
            description="Local in-memory map backed directory storage adapter.",
            type="storage",
            capabilities=["read", "write"],
            configuration={"storage_dir": "./data/local_store"},
            feature_flags={"enabled": True}
        )
        self._data: dict[str, Any] = {}

    @property
    def metadata(self) -> IntegrationMetadata:
        return self._metadata

    async def initialize(self) -> None:
        logger.info("Initializing Local Storage Adapter...")

    async def cleanup(self) -> None:
        logger.info("Cleaning up Local Storage Adapter resources...")
        self._data.clear()

    async def health_check(self) -> bool:
        return True

    async def read(self, key: str) -> Any:
        logger.info(f"Reading from Local Storage: {key}")
        return self._data.get(key)

    async def write(self, key: str, val: Any) -> None:
        logger.info(f"Writing to Local Storage: {key} = {val}")
        self._data[key] = val


class PostgreSQLStorageAdapter(IStorageAdapter):
    """
    PostgreSQL Database Storage Adapter.
    """
    def __init__(self) -> None:
        self._metadata = IntegrationMetadata(
            id="postgres-storage",
            name="PostgreSQL Database Client",
            version="1.0.0",
            description="PostgreSQL relational database client adapter framework.",
            type="storage",
            capabilities=["read", "write", "transactions"],
            configuration={"host": settings.DB_HOST, "port": settings.DB_PORT},
            feature_flags={"enabled": True}
        )

    @property
    def metadata(self) -> IntegrationMetadata:
        return self._metadata

    async def initialize(self) -> None:
        logger.info("Initializing PostgreSQL Storage Adapter...")

    async def cleanup(self) -> None:
        logger.info("Cleaning up PostgreSQL resources...")

    async def health_check(self) -> bool:
        return True

    async def read(self, key: str) -> Any:
        return {"id": key, "source": "postgres-stub", "data": "Relational record value"}

    async def write(self, key: str, val: Any) -> None:
        logger.info(f"Mock PostgreSQL write: {key} = {val}")


class RedisStorageAdapter(IStorageAdapter):
    """
    Redis Cache Storage Adapter.
    """
    def __init__(self) -> None:
        self._metadata = IntegrationMetadata(
            id="redis-storage",
            name="Redis Cache Client",
            version="1.0.0",
            description="Redis key-value cache and session tracker adapter framework.",
            type="storage",
            capabilities=["read", "write", "ttl"],
            configuration={"host": settings.REDIS_HOST, "port": settings.REDIS_PORT},
            feature_flags={"enabled": True}
        )

    @property
    def metadata(self) -> IntegrationMetadata:
        return self._metadata

    async def initialize(self) -> None:
        logger.info("Initializing Redis Storage Adapter...")

    async def cleanup(self) -> None:
        logger.info("Cleaning up Redis resources...")

    async def health_check(self) -> bool:
        return True

    async def read(self, key: str) -> Any:
        return f"Cached value for key: {key} (redis-stub)"

    async def write(self, key: str, val: Any) -> None:
        logger.info(f"Mock Redis write: {key} = {val}")


class VectorDBStorageAdapter(IStorageAdapter):
    """
    Vector Database (Chroma) Storage Adapter.
    """
    def __init__(self) -> None:
        self._metadata = IntegrationMetadata(
            id="vector-db-storage",
            name="Chroma Vector DB Client",
            version="1.0.0",
            description="Chroma vector database embedding and semantic lookup adapter framework.",
            type="storage",
            capabilities=["read", "write", "embeddings"],
            configuration={"host": settings.CHROMA_HOST, "port": settings.CHROMA_PORT},
            feature_flags={"enabled": True}
        )

    @property
    def metadata(self) -> IntegrationMetadata:
        return self._metadata

    async def initialize(self) -> None:
        logger.info("Initializing Vector DB Storage Adapter...")

    async def cleanup(self) -> None:
        logger.info("Cleaning up Vector DB resources...")

    async def health_check(self) -> bool:
        return True

    async def read(self, key: str) -> Any:
        return {"id": key, "distance": 0.02, "text": "Semantic document advisory context"}

    async def write(self, key: str, val: Any) -> None:
        logger.info(f"Mock Vector DB embedding write: {key} = {val}")


class CloudStorageAdapter(IStorageAdapter):
    """
    Cloud Storage Adapter (AWS S3, Azure Blob, Cloudflare R2).
    """
    def __init__(self) -> None:
        self._metadata = IntegrationMetadata(
            id="cloud-storage",
            name="Cloud Storage Provider Client",
            version="1.0.0",
            description="Production AWS S3 / Cloudflare R2 bucket integration adapter.",
            type="storage",
            capabilities=["read", "write", "cloud_bucket"],
            configuration={"bucket_name": settings.S3_BUCKET_NAME},
            feature_flags={"enabled": True}
        )
        self._local_cache: dict[str, Any] = {}

    @property
    def metadata(self) -> IntegrationMetadata:
        return self._metadata

    async def initialize(self) -> None:
        logger.info("Initializing Cloud Storage Adapter...")

    async def cleanup(self) -> None:
        logger.info("Cleaning up Cloud Storage resources...")
        self._local_cache.clear()

    async def health_check(self) -> bool:
        return bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)

    async def read(self, key: str) -> Any:
        logger.info(f"Reading from Cloud Storage: {key}")
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                import boto3
                s3 = boto3.client(
                    "s3",
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
                response = s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
                return response["Body"].read().decode("utf-8")
            except Exception as e:
                logger.warning(f"[CloudStorageAdapter] S3 read failed, using cache fallback: {e}")
        return self._local_cache.get(key, f"Mock cloud value for: {key}")

    async def write(self, key: str, val: Any) -> None:
        logger.info(f"Writing to Cloud Storage: {key}")
        self._local_cache[key] = val
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                import boto3
                s3 = boto3.client(
                    "s3",
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
                s3.put_object(Bucket=settings.S3_BUCKET_NAME, Key=key, Body=str(val))
            except Exception as e:
                logger.warning(f"[CloudStorageAdapter] S3 write failed: {e}")
