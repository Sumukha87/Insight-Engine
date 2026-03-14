# API & Frontend Rules

## FastAPI Conventions

- All route handlers are `async def`
- All request/response bodies are Pydantic v2 models in `src/api/schemas.py`
- Use `HTTPException` for client errors, let unhandled exceptions propagate to 500 handler
- Add Prometheus metrics to every endpoint:
  ```python
  from prometheus_client import Counter, Histogram
  REQUEST_COUNT = Counter("api_requests_total", "Total requests", ["endpoint"])
  REQUEST_LATENCY = Histogram("api_request_duration_seconds", "Latency", ["endpoint"])
  ```
- Health endpoint must return: `{"status": "ok", "neo4j": bool, "qdrant": bool, "ollama": bool}`

## Response Schema Standard

```python
class QueryResponse(BaseModel):
    answer: str
    paths: list[GraphPath]
    sources: list[SourceCitation]
    confidence: float
    latency_ms: int

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
```

## Next.js Static Hosting Conventions

- **Build Output:** `output: 'export'` in next.config.mjs (results in `/out` folder).
- **App Router:** Use `src/app/` but ensure all pages are static-compatible.
- **Data Fetching:**
    - Use **TanStack Query** exclusively (Client-side fetching only).
    - No `getServerSideProps` or dynamic `headers()`/`cookies()` in Server Components.
    - All pages must be exportable (use `export const dynamic = 'force-static'` if needed).
- **API Client:** `src/lib/api.ts` must use absolute URLs (e.g., `process.env.NEXT_PUBLIC_API_URL`) since there is no relative proxy/rewrite.
- **Images:** Use standard `<img>` or Next.js `<Image>` with `unoptimized: true`.
- **Routing:** Avoid `next/navigation` functions that rely on server-side logic (like `redirect` on the server); use client-side hooks instead.

## Sigma.js Graph Rendering Pattern

```typescript
import Sigma from "sigma";
import Graph from "graphology";

const graph = new Graph();
// Add nodes with domain-based colors
graph.addNode(id, { label, domain, x, y, size, color: DOMAIN_COLORS[domain] });
graph.addEdge(source, target, { label: relationType, size: confidence });

const renderer = new Sigma(graph, container, {
  renderEdgeLabels: false,  // performance
  defaultNodeColor: "#6B7280",
});
```

Domain color map:
```typescript
const DOMAIN_COLORS: Record<string, string> = {
  Aerospace:      "#185FA5",
  Medical:        "#0F6E56",
  Materials:      "#854F0B",
  Engineering:    "#534AB7",
  Pharma:         "#993C1D",
};
```
