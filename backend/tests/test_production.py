import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import Settings, validate_production_config

def test_liveness_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/v1/health/liveness")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "kisan-mitra-backend"

def test_readiness_endpoint_response_structure():
    with TestClient(app) as client:
        response = client.get("/api/v1/health/readiness")
        # In a local development context, database/cache/vector_db dependencies may be offline/unconnected.
        # Thus, readiness probe may return 200 (if connected) or 503 Service Unavailable (degraded).
        # We assert the HTTP status code is one of these and verify the payload contains the core components.
        assert response.status_code in [200, 503]
        
        data = response.json()
        if response.status_code == 503:
            assert "detail" in data
            data = data["detail"]
            
        assert data["service"] == "kisan-mitra-backend"
        assert "components" in data
        assert "database" in data["components"]
        assert "cache" in data["components"]
        assert "vector_db" in data["components"]

def test_validate_production_config_success():
    cfg = Settings(
        APP_ENV="production",
        DB_PASSWORD="super_secure_randomized_password_12345",
        DB_USER="custom_admin",
        DATABASE_URL="postgresql://custom_admin:super_secure_randomized_password_12345@db:5432/km_prod",
        FEATURE_LLM_ENABLED=True,
        DEFAULT_LLM_PROVIDER="gemini",
        GEMINI_API_KEY="AIzaSyValidApiKey",
        DEBUG=False
    )
    # Should complete without throwing ValueErrors
    validate_production_config(cfg)

def test_validate_production_config_fails_default_credentials():
    cfg = Settings(
        APP_ENV="production",
        DB_PASSWORD="postgres",
        DB_USER="postgres",
        DATABASE_URL="postgresql://postgres:postgres@db:5432/km_prod",
        DEBUG=False
    )
    with pytest.raises(ValueError) as excinfo:
        validate_production_config(cfg)
    assert "DB_PASSWORD" in str(excinfo.value) or "DATABASE_URL" in str(excinfo.value)

def test_validate_production_config_fails_debug_active():
    cfg = Settings(
        APP_ENV="production",
        DB_PASSWORD="super_secure_randomized_password_12345",
        DB_USER="custom_admin",
        DATABASE_URL="postgresql://custom_admin:super_secure_randomized_password_12345@db:5432/km_prod",
        DEBUG=True
    )
    with pytest.raises(ValueError) as excinfo:
        validate_production_config(cfg)
    assert "DEBUG" in str(excinfo.value)
