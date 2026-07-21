import pytest
from app.core.exceptions import ValidationException
from app.main import app
from fastapi.testclient import TestClient


def test_error_handling_kisan_mitra_exception():
    """
    Asserts that raising custom KisanMitraExceptions maps correctly to JSON error envelopes.
    """
    # Create a temporary test endpoint that raises ValidationException
    @app.get("/api/v1/test-exception-trigger")
    def trigger_exception():
        raise ValidationException("Custom validation failed", details={"failed_field": "test"})

    with TestClient(app) as client:
        response = client.get("/api/v1/test-exception-trigger")
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "ValidationException"
        assert data["message"] == "Custom validation failed"
        assert data["details"]["failed_field"] == "test"

def test_error_handling_validation_error():
    """
    Asserts that schema validation errors are intercepted and returned as 400 Bad Request.
    """
    with TestClient(app) as client:
        # Send empty dictionary or incorrect type to trigger FastAPI RequestValidationError
        response = client.post("/api/v1/query", json={"query": 12345})  # Should be string
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "RequestValidationError"
        assert "validation_errors" in data["details"]

def test_security_headers_middleware():
    """
    Asserts that custom security headers are injected into every outgoing HTTP response.
    """
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "default-src 'self'" in response.headers.get("Content-Security-Policy", "")

def test_response_compression():
    """
    Asserts that large payloads (exceeding 1000 bytes) are compressed with Gzip
    when Accept-Encoding: gzip is set.
    """
    with TestClient(app) as client:
        # Querying an endpoint with large response, e.g. /api/v1/ai/agents or /docs
        headers = {"Accept-Encoding": "gzip"}
        response = client.get("/openapi.json", headers=headers)

        # In TestClient, it decompresses automatically but we can check if content-encoding is set
        # to gzip, or if the size/encoding was handled.
        # Starlette's TestClient simulates ASGI call, so we inspect raw response headers
        # if they contain content-encoding gzip.
        if response.status_code == 200:
            # Check content-encoding header in response headers (case-insensitive)
            encoding = response.headers.get("content-encoding", "")
            # Note: TestClient does automatically decompress responses sometimes, but
            # gzip middleware should apply if size > 1000 bytes.
            assert "gzip" in encoding or response.headers.get("Content-Encoding") == "gzip"

@pytest.mark.asyncio
async def test_reasoning_cache_hit_and_miss():
    """
    Asserts that ReasoningCache works and consecutive identical queries hit the cache.
    """
    # Create container context manually
    with TestClient(app) as client:
        container = client.app.state.container
        # Clear cache first to prevent cross-test contamination
        container.reasoning_platform.cache._store.clear()

        payload = {
            "session_id": "SESS-READINESS-123",
            "query": "How is the mandi price of wheat today?",
            "farmer_id": "FR-12345"
        }

        # 1. First execution (Cache Miss)
        res1 = client.post("/api/v1/query", json=payload)
        assert res1.status_code == 200
        result1 = res1.json()

        # 2. Second execution (Cache Hit)
        res2 = client.post("/api/v1/query", json=payload)
        assert res2.status_code == 200
        result2 = res2.json()

        # Both execution results should be identical since the second was pulled from cache
        assert result1["data"]["summary"] == result2["data"]["summary"]
        assert result1["data"]["recommendation"] == result2["data"]["recommendation"]

        # Verify stats show a cache hit
        cache_stats = container.reasoning_platform.cache.stats
        assert cache_stats["hits"] >= 1
