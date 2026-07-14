"""
test_swagger_csp.py — Verification tests for Swagger UI endpoints & CSP header changes.
"""
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_openapi_json_loads() -> None:
    """GET /openapi.json returns successful JSON schema."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "openapi" in schema
    assert "paths" in schema

def test_docs_page_csp_header() -> None:
    """GET /docs returns HTML containing CDN links and the correct CSP header."""
    resp = client.get("/docs")
    assert resp.status_code == 200

    # Verify Content-Security-Policy headers allow jsdelivr and tiangolo
    csp = resp.headers.get("Content-Security-Policy", "")
    assert "https://cdn.jsdelivr.net" in csp
    assert "https://fastapi.tiangolo.com" in csp

    # Verify response body references SwaggerUIBundle
    html = resp.text
    assert "swagger-ui" in html.lower()

def test_redoc_page_csp_header() -> None:
    """GET /redoc returns HTML containing correct CSP header."""
    resp = client.get("/redoc")
    assert resp.status_code == 200

    csp = resp.headers.get("Content-Security-Policy", "")
    assert "https://cdn.jsdelivr.net" in csp
    assert "https://fastapi.tiangolo.com" in csp

    html = resp.text
    assert "redoc" in html.lower()
