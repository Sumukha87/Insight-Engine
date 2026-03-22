import asyncio
import hashlib
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

from src.backend.api.schemas import (ExploreEdge, ExploreNode,
                                     GraphExploreResponse, GraphNode,
                                     GraphPath, HealthResponse, HistoryItem,
                                     LoginRequest, QueryRequest, QueryResponse,
                                     RefreshRequest, RegisterRequest,
                                     SavedQueryItem, SaveQueryRequest,
                                     SessionResponse, SourceCitation,
                                     TokenResponse, TrendingEntity,
                                     UserResponse, WatchlistAddRequest,
                                     WatchlistItem)
from src.backend.auth.deps import CurrentUser, get_current_token
from src.backend.auth.security import (hash_password, hash_token,
                                       verify_password)
from src.backend.auth.token_service import (issue_tokens, refresh_tokens,
                                            revoke_session_by_token_hash)
from src.backend.db.crud import saved_queries as saved_queries_crud
from src.backend.db.crud import sessions as sessions_crud
from src.backend.db.crud import users as users_crud
from src.backend.db.crud import watchlist as watchlist_crud
from src.backend.db.session import get_db

# ── Prometheus ────────────────────────────────────────────────────────────────
REQUEST_COUNT = Counter("api_requests_total", "Total requests", ["endpoint"])
REQUEST_LATENCY = Histogram("api_request_duration_seconds", "Latency", ["endpoint"])

# GraphRAG quality metrics
GRAPHRAG_PATHS = Histogram(
    "graphrag_paths_found",
    "Cross-domain paths found per query",
    buckets=[0, 1, 5, 10, 20, 50, 100],
)
GRAPHRAG_SEEDS = Histogram(
    "graphrag_seeds_found",
    "Seed entities matched per query",
    buckets=[0, 1, 2, 3, 5, 10],
)
GRAPHRAG_CITATIONS = Histogram(
    "graphrag_citations_returned",
    "Source citations returned per query",
    buckets=[0, 5, 10, 20, 50],
)
GRAPHRAG_CONFIDENCE = Histogram(
    "graphrag_confidence_score",
    "Query confidence score",
    buckets=[0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0],
)

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
    return (
        forwarded.split(",")[0].strip()
        if forwarded
        else request.client.host if request.client else None
    )


# ── Auth routes ───────────────────────────────────────────────────────────────


@app.post(
    "/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    REQUEST_COUNT.labels(endpoint="/auth/register").inc()

    if await users_crud.get_by_email(db, body.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    user = await users_crud.create_user_with_org(
        db,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        org_name=body.org_name,
        job_title=body.job_title,
    )

    access_token, refresh_token = await issue_tokens(
        db,
        user,
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive"
        )

    await users_crud.update_last_login(db, user)

    access_token, refresh_token = await issue_tokens(
        db,
        user,
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
        db,
        body.refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
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
    qdrant_ok = await _check(
        f"http://{os.getenv('QDRANT_HOST', 'qdrant')}:{os.getenv('QDRANT_PORT', '6333')}/health"
    )
    ollama_ok = await _check(
        f"{os.getenv('OLLAMA_HOST', 'http://ollama:11434')}/api/tags"
    )

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
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query cannot be empty",
        )

    # run_query is CPU/IO bound (Neo4j + Ollama) — run in thread pool to avoid blocking
    from src.graph.graphrag_query import run_query

    loop = asyncio.get_event_loop()
    try:
        with REQUEST_LATENCY.labels(endpoint="/query").time():
            result = await loop.run_in_executor(
                None,
                partial(
                    run_query, body.query, top_k=body.top_k, max_paths=body.max_paths
                ),
            )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Query engine unavailable",
        ) from exc

    # Record GraphRAG quality metrics to Prometheus
    GRAPHRAG_PATHS.observe(len(result.paths))
    GRAPHRAG_SEEDS.observe(len(result.seed_entities))
    GRAPHRAG_CITATIONS.observe(len(result.sources))
    GRAPHRAG_CONFIDENCE.observe(result.confidence)

    # Log to MLflow graphrag-queries experiment (best-effort)
    try:
        import mlflow

        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        mlflow.set_tracking_uri(mlflow_uri)
        exp = mlflow.set_experiment("graphrag-queries")
        with mlflow.start_run(
            experiment_id=exp.experiment_id,
            run_name=f"query-{hashlib.md5(body.query.encode()).hexdigest()[:8]}",
        ):
            mlflow.log_param(
                "query_hash", hashlib.md5(body.query.encode()).hexdigest()[:8]
            )
            mlflow.log_param("top_k", body.top_k)
            mlflow.log_metric("paths_found", len(result.paths))
            mlflow.log_metric("seeds_found", len(result.seed_entities))
            mlflow.log_metric("citations_returned", len(result.sources))
            mlflow.log_metric("confidence", result.confidence)
            mlflow.log_metric("latency_ms", result.latency_ms)
    except Exception:
        pass  # never fail the response for MLflow

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
                nodes=[
                    GraphNode(name=n["name"], type=n["type"], domain=n["domain"])
                    for n in p.nodes
                ],
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


# ── Graph explore ──────────────────────────────────────────────────────────────


def _explore_entity(entity: str) -> dict:
    """Sync Neo4j query — runs in thread pool."""
    from neo4j import GraphDatabase as Neo4jDriver

    neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.environ["NEO4J_PASSWORD"]

    driver = Neo4jDriver.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    try:
        with driver.session() as session:
            records = session.run(
                """
                MATCH (center:Entity {name: $entity})
                WITH center LIMIT 1
                MATCH (center)-[r:RELATES_TO]-(neighbor:Entity)
                RETURN
                  center.name  AS center_name,
                  center.type  AS center_type,
                  center.domain AS center_domain,
                  neighbor.name  AS neighbor_name,
                  neighbor.type  AS neighbor_type,
                  neighbor.domain AS neighbor_domain,
                  r.relation AS relation,
                  CASE WHEN startNode(r) = center THEN center.name ELSE neighbor.name END AS source,
                  CASE WHEN startNode(r) = center THEN neighbor.name ELSE center.name END AS target
                LIMIT 50
                """,
                entity=entity,
            ).data()
    finally:
        driver.close()

    if not records:
        return {"center": entity, "nodes": [], "edges": []}

    nodes_map: dict[str, dict] = {}
    edges: list[dict] = []

    first = records[0]
    nodes_map[first["center_name"]] = {
        "name": first["center_name"],
        "type": first["center_type"],
        "domain": first["center_domain"],
        "is_center": True,
    }

    for rec in records:
        if rec["neighbor_name"] and rec["neighbor_name"] not in nodes_map:
            nodes_map[rec["neighbor_name"]] = {
                "name": rec["neighbor_name"],
                "type": rec["neighbor_type"],
                "domain": rec["neighbor_domain"],
                "is_center": False,
            }
        if rec["source"] and rec["target"]:
            edges.append(
                {
                    "source": rec["source"],
                    "target": rec["target"],
                    "relation": rec["relation"] or "RELATES_TO",
                }
            )

    return {"center": entity, "nodes": list(nodes_map.values()), "edges": edges}


@app.get("/graph/explore", response_model=GraphExploreResponse)
async def graph_explore(
    entity: str,
    current_user: CurrentUser,
) -> GraphExploreResponse:
    REQUEST_COUNT.labels(endpoint="/graph/explore").inc()

    if not entity.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="entity cannot be empty",
        )

    loop = asyncio.get_event_loop()
    try:
        with REQUEST_LATENCY.labels(endpoint="/graph/explore").time():
            result = await loop.run_in_executor(None, partial(_explore_entity, entity))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph exploration unavailable",
        ) from exc

    return GraphExploreResponse(
        center=result["center"],
        nodes=[ExploreNode(**n) for n in result["nodes"]],
        edges=[ExploreEdge(**e) for e in result["edges"]],
    )


# ── Saved queries ──────────────────────────────────────────────────────────────


@app.post(
    "/queries/save", response_model=SavedQueryItem, status_code=status.HTTP_201_CREATED
)
async def save_query(
    body: SaveQueryRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> SavedQueryItem:
    REQUEST_COUNT.labels(endpoint="/queries/save").inc()
    sq = await saved_queries_crud.create(
        db,
        user_id=current_user.id,
        name=body.name,
        query_text=body.query_text,
        result_json=body.result,
        notes=body.notes,
    )
    return SavedQueryItem.model_validate(sq)


@app.get("/queries/saved", response_model=list[SavedQueryItem])
async def list_saved_queries(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[SavedQueryItem]:
    REQUEST_COUNT.labels(endpoint="/queries/saved").inc()
    rows = await saved_queries_crud.list_for_user(db, current_user.id)
    return [SavedQueryItem.model_validate(r) for r in rows]


@app.delete("/queries/saved/{sq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_query(
    sq_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    REQUEST_COUNT.labels(endpoint="/queries/saved/{id}").inc()
    sq = await saved_queries_crud.get_by_id(db, sq_id)
    if sq is None or sq.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved query not found"
        )
    await saved_queries_crud.delete(db, sq)


# ── Query history ──────────────────────────────────────────────────────────────


@app.get("/queries/history", response_model=list[HistoryItem])
async def query_history(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[HistoryItem]:
    REQUEST_COUNT.labels(endpoint="/queries/history").inc()
    rows = await db.execute(
        text(
            "SELECT id, query_text, latency_ms, created_at FROM query_logs "
            "WHERE user_id = :uid ORDER BY created_at DESC LIMIT 50"
        ),
        {"uid": str(current_user.id)},
    )
    return [
        HistoryItem(
            id=r.id,
            query_text=r.query_text,
            latency_ms=r.latency_ms,
            created_at=r.created_at,
        )
        for r in rows
    ]


# ── Watchlist ──────────────────────────────────────────────────────────────────


@app.post(
    "/watchlist", response_model=WatchlistItem, status_code=status.HTTP_201_CREATED
)
async def add_to_watchlist(
    body: WatchlistAddRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> WatchlistItem:
    REQUEST_COUNT.labels(endpoint="/watchlist").inc()
    item = await watchlist_crud.add(
        db,
        user_id=current_user.id,
        entity_name=body.entity_name,
        entity_type=body.entity_type,
        entity_domain=body.entity_domain,
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Entity already on watchlist"
        )
    return WatchlistItem.model_validate(item)


@app.get("/watchlist", response_model=list[WatchlistItem])
async def get_watchlist(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[WatchlistItem]:
    REQUEST_COUNT.labels(endpoint="/watchlist").inc()
    items = await watchlist_crud.list_for_user(db, current_user.id)
    return [WatchlistItem.model_validate(i) for i in items]


@app.delete("/watchlist/{entity_name}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    entity_name: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    REQUEST_COUNT.labels(endpoint="/watchlist/{name}").inc()
    removed = await watchlist_crud.remove(db, current_user.id, entity_name)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Entity not on watchlist"
        )


# ── Trending ───────────────────────────────────────────────────────────────────


def _fetch_trending() -> list[dict]:
    """Top entities by cross-domain RELATES_TO connections — runs in thread pool."""
    from neo4j import GraphDatabase as Neo4jDriver

    neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.environ["NEO4J_PASSWORD"]

    driver = Neo4jDriver.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    try:
        with driver.session() as session:
            records = session.run("""
                MATCH (e:Entity)-[r:RELATES_TO]-(other:Entity)
                WHERE e.domain <> other.domain
                WITH e, count(DISTINCT other) AS cross_domain_connections
                ORDER BY cross_domain_connections DESC
                RETURN e.name AS name, e.domain AS domain, e.type AS type,
                       cross_domain_connections
                LIMIT 30
                """).data()
    finally:
        driver.close()
    return records


@app.get("/trending", response_model=list[TrendingEntity])
async def trending(current_user: CurrentUser) -> list[TrendingEntity]:
    REQUEST_COUNT.labels(endpoint="/trending").inc()
    loop = asyncio.get_event_loop()
    try:
        with REQUEST_LATENCY.labels(endpoint="/trending").time():
            records = await loop.run_in_executor(None, _fetch_trending)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trending unavailable",
        ) from exc
    return [TrendingEntity(**r) for r in records]
