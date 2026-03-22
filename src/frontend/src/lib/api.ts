const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Store tokens in both localStorage (for API calls) and a cookie (for middleware). */
export function saveTokens(access_token: string, refresh_token: string) {
  localStorage.setItem("access_token", access_token);
  localStorage.setItem("refresh_token", refresh_token);
  // Middleware reads this cookie to determine auth state
  document.cookie = `access_token=${access_token}; path=/; SameSite=Lax`;
}

/** Clear all auth state on logout. */
export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  document.cookie = "access_token=; path=/; max-age=0";
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  job_title: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface ApiError {
  detail: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const data = await res.json();
  if (!res.ok) {
    const detail = (data as any).detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
        ? detail.map((d: any) => d.msg ?? JSON.stringify(d)).join(", ")
        : "Request failed";
    throw new Error(message);
  }
  return data as T;
}

export const api = {
  register(body: {
    email: string;
    password: string;
    full_name: string;
    org_name: string;
    job_title?: string;
  }): Promise<TokenResponse> {
    return request("/auth/register", { method: "POST", body: JSON.stringify(body) });
  },

  login(body: { email: string; password: string }): Promise<TokenResponse> {
    return request("/auth/login", { method: "POST", body: JSON.stringify(body) });
  },

  refresh(refresh_token: string): Promise<TokenResponse> {
    return request("/auth/refresh", { method: "POST", body: JSON.stringify({ refresh_token }) });
  },

  me(access_token: string): Promise<UserResponse> {
    return request("/auth/me", { headers: { Authorization: `Bearer ${access_token}` } });
  },

  logout(access_token: string): Promise<void> {
    return request("/auth/logout", {
      method: "POST",
      headers: { Authorization: `Bearer ${access_token}` },
    });
  },

  query(
    access_token: string,
    body: { query: string; top_k?: number; max_paths?: number }
  ): Promise<QueryResponse> {
    return request("/query", {
      method: "POST",
      headers: { Authorization: `Bearer ${access_token}` },
      body: JSON.stringify(body),
    });
  },

  explore(access_token: string, entity: string): Promise<GraphExploreResponse> {
    return request(`/graph/explore?entity=${encodeURIComponent(entity)}`, {
      headers: { Authorization: `Bearer ${access_token}` },
    });
  },

  saveQuery(
    access_token: string,
    body: { name: string; query_text: string; result: QueryResponse; notes?: string }
  ): Promise<SavedQueryItem> {
    return request("/queries/save", {
      method: "POST",
      headers: { Authorization: `Bearer ${access_token}` },
      body: JSON.stringify(body),
    });
  },

  listSaved(access_token: string): Promise<SavedQueryItem[]> {
    return request("/queries/saved", { headers: { Authorization: `Bearer ${access_token}` } });
  },

  deleteSaved(access_token: string, id: string): Promise<void> {
    return request(`/queries/saved/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${access_token}` },
    });
  },

  history(access_token: string): Promise<HistoryItem[]> {
    return request("/queries/history", { headers: { Authorization: `Bearer ${access_token}` } });
  },

  addWatchlist(
    access_token: string,
    body: { entity_name: string; entity_type: string; entity_domain: string }
  ): Promise<WatchlistItem> {
    return request("/watchlist", {
      method: "POST",
      headers: { Authorization: `Bearer ${access_token}` },
      body: JSON.stringify(body),
    });
  },

  getWatchlist(access_token: string): Promise<WatchlistItem[]> {
    return request("/watchlist", { headers: { Authorization: `Bearer ${access_token}` } });
  },

  removeWatchlist(access_token: string, entity_name: string): Promise<void> {
    return request(`/watchlist/${encodeURIComponent(entity_name)}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${access_token}` },
    });
  },

  trending(access_token: string): Promise<TrendingEntity[]> {
    return request("/trending", { headers: { Authorization: `Bearer ${access_token}` } });
  },
};

export interface GraphNode {
  name: string;
  type: string;
  domain: string;
}

export interface SavedQueryItem {
  id: string;
  name: string;
  query_text: string;
  notes: string | null;
  created_at: string;
  result: QueryResponse;
}

export interface HistoryItem {
  id: string;
  query_text: string;
  latency_ms: number | null;
  created_at: string;
}

export interface WatchlistItem {
  id: string;
  entity_name: string;
  entity_type: string;
  entity_domain: string;
  added_at: string;
}

export interface TrendingEntity {
  name: string;
  domain: string;
  type: string;
  cross_domain_connections: number;
}

export interface ExploreNode {
  name: string;
  type: string;
  domain: string;
  is_center: boolean;
}

export interface ExploreEdge {
  source: string;
  target: string;
  relation: string;
}

export interface GraphExploreResponse {
  center: string;
  nodes: ExploreNode[];
  edges: ExploreEdge[];
}

export interface GraphPath {
  nodes: GraphNode[];
  relations: string[];
  hops: number;
}

export interface SourceCitation {
  doc_id: string;
  title: string;
  year: number;
  doi: string | null;
  domain: string | null;
}

export interface QueryResponse {
  answer: string;
  paths: GraphPath[];
  seed_entities: string[];
  sources: SourceCitation[];
  confidence: number;
  latency_ms: number;
}
