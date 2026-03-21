const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error((data as ApiError).detail ?? "Request failed");
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
};
