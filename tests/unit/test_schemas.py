"""
Unit tests for src/backend/api/schemas.py

Tests Pydantic v2 validation rules without any external services.
"""

import pytest
from pydantic import ValidationError

from src.backend.api.schemas import (LoginRequest, QueryRequest,
                                     RegisterRequest, SaveQueryRequest,
                                     WatchlistAddRequest)

VALID_PW = "strongpassword"
SHORT_PW = "short"
EXACT_PW = "exactly8"
VALID_EMAIL = "user@example.com"
BAD_EMAIL = "not-an-email"


class TestRegisterRequest:
    def test_valid_registration(self):
        req = RegisterRequest(
            email=VALID_EMAIL,
            password=VALID_PW,
            full_name="Test User",
            org_name="ACME Corp",
        )
        assert req.email == VALID_EMAIL
        assert req.full_name == "Test User"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email=BAD_EMAIL,
                password=VALID_PW,
                full_name="Test User",
                org_name="ACME Corp",
            )

    def test_short_password_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email=VALID_EMAIL,
                password=SHORT_PW,
                full_name="Test User",
                org_name="ACME Corp",
            )
        assert "8 characters" in str(exc_info.value)

    def test_password_exactly_8_chars_accepted(self):
        req = RegisterRequest(
            email=VALID_EMAIL,
            password=EXACT_PW,
            full_name="Test User",
            org_name="ACME Corp",
        )
        assert req.password == EXACT_PW

    def test_optional_job_title_defaults_none(self):
        req = RegisterRequest(
            email=VALID_EMAIL,
            password=VALID_PW,
            full_name="Test User",
            org_name="ACME Corp",
        )
        assert req.job_title is None

    def test_optional_job_title_accepted(self):
        req = RegisterRequest(
            email=VALID_EMAIL,
            password=VALID_PW,
            full_name="Test User",
            org_name="ACME Corp",
            job_title="Researcher",
        )
        assert req.job_title == "Researcher"


class TestLoginRequest:
    def test_valid_login(self):
        req = LoginRequest(email=VALID_EMAIL, password=VALID_PW)
        assert req.email == VALID_EMAIL

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(email=BAD_EMAIL, password=VALID_PW)


class TestQueryRequest:
    def test_valid_query(self):
        req = QueryRequest(query="aerospace materials for cardiac implants")
        assert req.query == "aerospace materials for cardiac implants"

    def test_empty_query_rejected(self):
        with pytest.raises(ValidationError):
            QueryRequest(query="")

    def test_default_max_paths(self):
        req = QueryRequest(query="test query")
        assert req.max_paths == 20

    def test_custom_max_paths(self):
        req = QueryRequest(query="test query", max_paths=5)
        assert req.max_paths == 5


class TestSaveQueryRequest:
    def test_valid_save_request(self):
        req = SaveQueryRequest(
            name="My research",
            query_text="aerospace materials",
            result={"answer": "test", "paths": []},
        )
        assert req.name == "My research"

    def test_notes_optional(self):
        req = SaveQueryRequest(
            name="Research",
            query_text="query",
            result={},
        )
        assert req.notes is None


class TestWatchlistAddRequest:
    def test_valid_watchlist_item(self):
        req = WatchlistAddRequest(
            entity_name="titanium alloy",
            entity_type="Material",
            entity_domain="Aerospace",
        )
        assert req.entity_name == "titanium alloy"
        assert req.entity_type == "Material"
