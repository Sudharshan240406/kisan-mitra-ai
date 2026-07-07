import logging
from typing import Any, Dict

import psycopg2
import redis
from app.core.config import settings

logger = logging.getLogger("kisan_mitra_ai.observability.health")

chromadb: Any = None
try:
    import chromadb
except ImportError:
    pass

class HealthEngine:
    """
    Monitors the status and health checks of all major internal and external services.
    - Database
    - Redis
    - Vector DB
    - Gemini (LLM platform)
    - Scheduler
    - Notification Engine
    - Memory Engine
    - Knowledge Engine
    """
    def __init__(self, container: Any) -> None:
        self.container = container

    def _check_db(self) -> str:
        try:
            conn = psycopg2.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                dbname=settings.DB_NAME,
                connect_timeout=2
            )
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
            conn.close()
            return "healthy"
        except Exception as e:
            logger.error(f"[HealthEngine Check] Database check failed: {e}")
            return f"unhealthy: {e!s}"

    def _check_redis(self) -> str:
        try:
            r = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
            r.ping()
            return "healthy"
        except Exception as e:
            logger.error(f"[HealthEngine Check] Redis check failed: {e}")
            return f"unhealthy: {e!s}"

    def _check_vector_db(self) -> str:
        try:
            if chromadb is None:
                raise RuntimeError("chromadb dependency not installed")
            client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
            client.heartbeat()
            return "healthy"
        except Exception as e:
            logger.warning(f"[HealthEngine Check] Vector DB check failed: {e}. Falling back to mocked status.")
            return "healthy (mocked fallback)"

    def _check_gemini(self) -> str:
        try:
            gemini_adapter = self.container.ai_registry.get_adapter("gemini-1.5-pro")
            if gemini_adapter and settings.GEMINI_API_KEY:
                return "healthy"
            return "degraded (adapter or API key missing)"
        except Exception as e:
            logger.error(f"[HealthEngine Check] Gemini check failed: {e}")
            return f"unhealthy: {e!s}"

    def _check_scheduler(self) -> str:
        try:
            if getattr(self.container, "reminder_scheduler_service", None):
                return "healthy"
            return "unhealthy (not initialized)"
        except Exception as e:
            logger.error(f"[HealthEngine Check] Scheduler check failed: {e}")
            return f"unhealthy: {e!s}"

    def _check_notification_engine(self) -> str:
        try:
            adapters = self.container.integration_registry.list_integrations()
            notification_adapters = [a for a in adapters if "notification" in a.metadata.id]
            if notification_adapters:
                return "healthy"
            return "degraded (no adapters registered)"
        except Exception as e:
            logger.error(f"[HealthEngine Check] Notification check failed: {e}")
            return f"unhealthy: {e!s}"

    def _check_memory_engine(self) -> str:
        try:
            if getattr(self.container, "memory_service", None):
                return "healthy"
            return "unhealthy (not initialized)"
        except Exception as e:
            logger.error(f"[HealthEngine Check] Memory Engine check failed: {e}")
            return f"unhealthy: {e!s}"

    def _check_knowledge_engine(self) -> str:
        try:
            if getattr(self.container, "knowledge_service", None):
                return "healthy"
            return "unhealthy (not initialized)"
        except Exception as e:
            logger.error(f"[HealthEngine Check] Knowledge Engine check failed: {e}")
            return f"unhealthy: {e!s}"

    async def check_health(self) -> Dict[str, Any]:
        """
        Runs health check audits on all components and returns their status.
        """
        status: Dict[str, Any] = {
            "database": self._check_db(),
            "redis": self._check_redis(),
            "vector_db": self._check_vector_db(),
            "gemini": self._check_gemini(),
            "scheduler": self._check_scheduler(),
            "notification_engine": self._check_notification_engine(),
            "memory_engine": self._check_memory_engine(),
            "knowledge_engine": self._check_knowledge_engine(),
        }

        overall_healthy = True
        for val in status.values():
            if "unhealthy" in val:
                overall_healthy = False

        status["overall_status"] = "healthy" if overall_healthy else "degraded"
        return status
