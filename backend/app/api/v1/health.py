import logging

import psycopg2
import redis
from app.core.config import settings
from app.schemas.responses import HealthResponse
from fastapi import APIRouter, HTTPException, status

try:
    import chromadb
except ModuleNotFoundError:
    chromadb = None

logger = logging.getLogger("kisan_mitra_ai")
router = APIRouter()

@router.get("/liveness", response_model=dict[str, str])
def check_liveness() -> dict[str, str]:
    """
    Liveness probe. Quick heartbeat to ensure application process is running.
    """
    return {"status": "healthy", "service": "kisan-mitra-backend"}

@router.get("/readiness", response_model=HealthResponse)
def check_readiness() -> HealthResponse:
    """
    Readiness probe. Checks connections to core dependencies (DB, Redis, Chroma).
    """
    components = {}
    is_healthy = True

    # 1. Audit PostgreSQL Database Connection
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            dbname=settings.DB_NAME,
            connect_timeout=3
        )
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
        conn.close()
        components["database"] = "healthy"
    except Exception as e:
        logger.error(f"[HEALTH CHECK FAIL] Database connection check failed: {e}")
        components["database"] = "unhealthy"
        is_healthy = False

    # 2. Audit Redis Cache Connection
    try:
        r = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=3)
        r.ping()
        components["cache"] = "healthy"
    except Exception as e:
        logger.error(f"[HEALTH CHECK FAIL] Redis connection check failed: {e}")
        components["cache"] = "unhealthy"
        is_healthy = False

    # 3. Audit Chroma Vector Database Connection
    try:
        if chromadb is None:
            raise RuntimeError("chromadb dependency not installed")
        client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        client.heartbeat()
        components["vector_db"] = "healthy"
    except Exception as e:
        logger.error(f"[HEALTH CHECK FAIL] Chroma Vector DB connection check failed: {e}")
        components["vector_db"] = "unhealthy"
        is_healthy = False

    overall_status = "healthy" if is_healthy else "degraded"

    response_payload = HealthResponse(
        status=overall_status,
        service="kisan-mitra-backend",
        components=components
    )

    if not is_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response_payload.model_dump()
        )

    return response_payload
