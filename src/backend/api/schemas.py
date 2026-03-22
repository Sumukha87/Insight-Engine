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

class GraphNode(BaseModel):
    name: str
    type: str
    domain: str


class GraphPath(BaseModel):
    nodes: list[GraphNode]
    relations: list[str]
    hops: int


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    max_paths: int = 20


class SourceCitation(BaseModel):
    doc_id: str
    title: str
    year: int
    doi: str | None
    domain: str | None


class QueryResponse(BaseModel):
    answer: str
    paths: list[GraphPath]
    seed_entities: list[str]
    sources: list[SourceCitation]
    confidence: float
    latency_ms: int


# ── Saved queries ─────────────────────────────────────────────────────────────

class SaveQueryRequest(BaseModel):
    name: str
    query_text: str
    result: dict          # full QueryResponse serialised as dict
    notes: str | None = None


class SavedQueryItem(BaseModel):
    id: uuid.UUID
    name: str
    query_text: str
    notes: str | None
    created_at: datetime
    result: dict

    model_config = {"from_attributes": True}


# ── History ───────────────────────────────────────────────────────────────────

class HistoryItem(BaseModel):
    id: uuid.UUID
    query_text: str
    latency_ms: int | None
    created_at: datetime


# ── Watchlist ─────────────────────────────────────────────────────────────────

class WatchlistAddRequest(BaseModel):
    entity_name: str
    entity_type: str
    entity_domain: str


class WatchlistItem(BaseModel):
    id: uuid.UUID
    entity_name: str
    entity_type: str
    entity_domain: str
    added_at: datetime

    model_config = {"from_attributes": True}


# ── Trending ──────────────────────────────────────────────────────────────────

class TrendingEntity(BaseModel):
    name: str
    domain: str
    type: str
    cross_domain_connections: int


# ── Graph explore ─────────────────────────────────────────────────────────────

class ExploreNode(BaseModel):
    name: str
    type: str
    domain: str
    is_center: bool = False


class ExploreEdge(BaseModel):
    source: str
    target: str
    relation: str


class GraphExploreResponse(BaseModel):
    center: str
    nodes: list[ExploreNode]
    edges: list[ExploreEdge]


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    neo4j: bool
    qdrant: bool
    ollama: bool
    postgres: bool
