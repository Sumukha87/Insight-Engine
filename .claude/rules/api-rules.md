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

## Next.js Conventions

- `src/app/` App Router structure
- `src/components/` — reusable UI components (shadcn/ui based)
- `src/lib/` — utility functions and API client
- `src/store/` — Zustand stores
- All API calls through `src/lib/api.ts` client (never fetch directly in components)
- Use TanStack Query for all server state — no `useState` + `useEffect` for fetching
- TypeScript strict mode: no `any` types

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
