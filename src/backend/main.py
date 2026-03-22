import asyncio
import os
import uuid
from datetime import datetime, timezone
from functools import partial

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, make_asgi_app
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.schemas import (
    GraphNode,
    GraphPath,
    HealthResponse,
    LoginRequest,
    QueryRequest,
    QueryResponse,
    RefreshRequest,
    RegisterRequest,
    SessionResponse,
    SourceCitation,
    TokenResponse,
    UserResponse,
)
from src.backend.auth.deps import CurrentUser, get_current_token
from src.backend.auth.security import hash_token, hash_password, verify_password
from src.backend.auth.token_service import (
    issue_tokens,
    refresh_tokens,
    revoke_session_by_token_hash,
)
from src.backend.db.crud import sessions as sessions_crud
from src.backend.db.crud import users as users_crud
from src.backend.db.session import get_db

# ── Prometheus ────────────────────────────────────────────────────────────────
REQUEST_COUNT = Counter("api_requests_total", "Total requests", ["endpoint"])
REQUEST_LATENCY = Histogram("api_request_duration_seconds", "Latency", ["endpoint"])

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Insight Engine API",
    version="0.1.0",
    description="Cross-domain innovation discovery via GraphRAG",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    return forwarded.split(",")[0].strip() if forwarded else request.client.host if request.client else None


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    REQUEST_COUNT.labels(endpoint="/auth/register").inc()

    if await users_crud.get_by_email(db, body.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = await users_crud.create_user_with_org(
        db,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        org_name=body.org_name,
        job_title=body.job_title,
    )

    access_token, refresh_token = await issue_tokens(
        db, user,
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@app.post("/auth/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    REQUEST_COUNT.labels(endpoint="/auth/login").inc()

    user = await users_crud.get_by_email(db, body.email)
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")

    await users_crud.update_last_login(db, user)

    access_token, refresh_token = await issue_tokens(
        db, user,
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@app.post("/auth/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    REQUEST_COUNT.labels(endpoint="/auth/refresh").inc()

    result = await refresh_tokens(
        db, body.refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    access_token, new_refresh_token = result
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: CurrentUser,
    token: str = Depends(get_current_token),
    db: AsyncSession = Depends(get_db),
) -> None:
    REQUEST_COUNT.labels(endpoint="/auth/logout").inc()
    await revoke_session_by_token_hash(db, hash_token(token))


@app.get("/auth/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    REQUEST_COUNT.labels(endpoint="/auth/me").inc()
    return UserResponse.model_validate(current_user)


@app.get("/auth/sessions", response_model=list[SessionResponse])
async def list_sessions(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[SessionResponse]:
    REQUEST_COUNT.labels(endpoint="/auth/sessions").inc()
    sessions = await sessions_crud.list_active_for_user(db, current_user.id)
    return [SessionResponse.model_validate(s) for s in sessions]


@app.delete("/auth/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    REQUEST_COUNT.labels(endpoint="/auth/sessions/{id}").inc()
    session = await sessions_crud.get_by_id(db, session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    await sessions_crud.revoke(db, session)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    REQUEST_COUNT.labels(endpoint="/health").inc()

    try:
        await db.execute(text("SELECT 1"))
        pg_ok = True
    except Exception:
        pg_ok = False

    async def _check(url: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(url)
                return r.status_code < 500
        except Exception:
            return False

    neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    neo4j_host = neo4j_uri.split("//")[-1].split(":")[0]  # handles bolt://host:port
    neo4j_ok = await _check(f"http://{neo4j_host}:7474")
    qdrant_ok = await _check(f"http://{os.getenv('QDRANT_HOST', 'qdrant')}:{os.getenv('QDRANT_PORT', '6333')}/health")
    ollama_ok = await _check(f"{os.getenv('OLLAMA_HOST', 'http://ollama:11434')}/api/tags")

    return HealthResponse(
        status="ok" if all([pg_ok, neo4j_ok, qdrant_ok, ollama_ok]) else "degraded",
        neo4j=neo4j_ok,
        qdrant=qdrant_ok,
        ollama=ollama_ok,
        postgres=pg_ok,
    )


# ── Query ─────────────────────────────────────────────────────────────────────

@app.post("/query", response_model=QueryResponse)
async def query(
    body: QueryRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> QueryResponse:
    REQUEST_COUNT.labels(endpoint="/query").inc()

    if not body.query.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Query cannot be empty")

    # run_query is CPU/IO bound (Neo4j + Ollama) — run in thread pool to avoid blocking
    from src.graph.graphrag_query import run_query
    loop = asyncio.get_event_loop()
    try:
        with REQUEST_LATENCY.labels(endpoint="/query").time():
            result = await loop.run_in_executor(
                None,
                partial(run_query, body.query, top_k=body.top_k, max_paths=body.max_paths),
            )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Query engine unavailable") from exc

    # Log to query_logs (best-effort — don't fail the response if logging fails)
    try:
        await db.execute(
            text(
                "INSERT INTO query_logs (id, user_id, query_text, latency_ms, created_at) "
                "VALUES (:id, :user_id, :query_text, :latency_ms, :created_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "user_id": str(current_user.id),
                "query_text": body.query,
                "latency_ms": result.latency_ms,
                "created_at": datetime.now(timezone.utc),
            },
        )
        await db.commit()
    except Exception:
        pass

    return QueryResponse(
        answer=result.answer,
        paths=[
            GraphPath(
                nodes=[GraphNode(name=n["name"], type=n["type"], domain=n["domain"]) for n in p.nodes],
                relations=p.relations,
                hops=p.hops,
            )
            for p in result.paths
        ],
        seed_entities=result.seed_entities,
        sources=[
            SourceCitation(
                doc_id=s.doc_id,
                title=s.title,
                year=s.year,
                doi=s.doi,
                domain=s.domain,
            )
            for s in result.sources
        ],
        confidence=result.confidence,
        latency_ms=result.latency_ms,
    )
