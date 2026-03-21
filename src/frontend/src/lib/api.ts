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
};

export interface GraphNode {
  name: string;
  type: string;
  domain: string;
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
