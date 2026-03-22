"""
Integration tests for the FastAPI backend.

These tests require the API container to be running:
    docker compose up -d api

Run with:
    pytest tests/integration/ -v -m integration
"""

import os

import httpx
import pytest

API_URL = os.environ.get("API_URL", "http://localhost:8000")


@pytest.mark.integration
class TestHealthEndpoint:
    def test_health_returns_200(self):
        resp = httpx.get(f"{API_URL}/health", timeout=10)
        assert resp.status_code == 200

    def test_health_has_status_ok(self):
        resp = httpx.get(f"{API_URL}/health", timeout=10)
        data = resp.json()
        assert data["status"] == "ok"

    def test_health_reports_service_statuses(self):
        resp = httpx.get(f"{API_URL}/health", timeout=10)
        data = resp.json()
        # All 4 required keys must be present per api-rules.md
        for key in ("status", "neo4j", "qdrant", "ollama"):
            assert key in data, f"Missing key '{key}' from /health response"

    def test_health_postgres_key_present(self):
        resp = httpx.get(f"{API_URL}/health", timeout=10)
        data = resp.json()
        assert "postgres" in data


@pytest.mark.integration
class TestMetricsEndpoint:
    def test_metrics_returns_200(self):
        resp = httpx.get(f"{API_URL}/metrics", timeout=10)
        assert resp.status_code == 200

    def test_metrics_contains_api_requests_total(self):
        resp = httpx.get(f"{API_URL}/metrics", timeout=10)
        assert "api_requests_total" in resp.text

    def test_metrics_contains_request_duration(self):
        resp = httpx.get(f"{API_URL}/metrics", timeout=10)
        assert "api_request_duration_seconds" in resp.text


@pytest.mark.integration
class TestAuthEndpoints:
    def test_register_rejects_weak_input(self):
        resp = httpx.post(
            f"{API_URL}/auth/register",
            json={
                "email": "bad-email",
                "password": "pw",
                "full_name": "Test",
                "org_name": "Test Org",
            },
            timeout=10,
        )
        assert resp.status_code == 422

    def test_login_rejects_unknown_user(self):
        resp = httpx.post(
            f"{API_URL}/auth/login",
            json={"email": "nobody@nowhere.invalid", "password": "doesnotmatter"},
            timeout=10,
        )
        assert resp.status_code in (401, 422)

    def test_protected_endpoint_requires_auth(self):
        resp = httpx.get(f"{API_URL}/auth/me", timeout=10)
        assert resp.status_code == 401
