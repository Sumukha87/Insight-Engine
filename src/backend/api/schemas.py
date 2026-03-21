import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    org_name: str
    job_title: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    job_title: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: uuid.UUID
    user_agent: str | None
    ip_address: str | None
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


# ── GraphRAG query ────────────────────────────────────────────────────────────

class GraphPath(BaseModel):
    nodes: list[str]
    edges: list[str]
    domains: list[str]


class SourceCitation(BaseModel):
    doc_id: str
    title: str
    year: int
    doi: str | None
    relevance_score: float


class QueryRequest(BaseModel):
    query: str
    target_domain: str | None = None
    max_paths: int = 20


class QueryResponse(BaseModel):
    answer: str
    paths: list[GraphPath]
    sources: list[SourceCitation]
    confidence: float
    latency_ms: int


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    neo4j: bool
    qdrant: bool
    ollama: bool
    postgres: bool
