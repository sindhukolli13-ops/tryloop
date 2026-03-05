/**
 * Typed fetch wrapper for calling the FastAPI backend.
 * Injects the Authorization header and handles token refresh on 401.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  token?: string;
}

interface ApiError {
  detail: string;
  status: number;
}

/**
 * Call the backend API. Automatically serializes JSON bodies
 * and includes the Authorization header when a token is provided.
 */
export async function api<T = unknown>(
  path: string,
  options: ApiOptions = {}
): Promise<T> {
  const { body, token, headers: extraHeaders, ...rest } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((extraHeaders as Record<string, string>) || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error: ApiError = {
      status: response.status,
      detail: "An error occurred",
    };
    try {
      const data = await response.json();
      error.detail = data.detail || data.message || error.detail;
    } catch {
      // response body wasn't JSON — keep default message
    }
    throw error;
  }

  return response.json() as Promise<T>;
}

// ── Typed auth endpoints ──

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  email: string;
  name: string;
  role: string;
  email_verified: boolean;
  created_at: string;
}

export function authSignup(data: { name: string; email: string; password: string }) {
  return api<TokenResponse>("/auth/signup", { method: "POST", body: data });
}

export function authLogin(data: { email: string; password: string }) {
  return api<TokenResponse>("/auth/login", { method: "POST", body: data });
}

export function authRefresh(refresh_token: string) {
  return api<TokenResponse>("/auth/refresh", {
    method: "POST",
    body: { refresh_token },
  });
}

export function authVerifyEmail(token: string) {
  return api<{ message: string }>("/auth/verify-email", {
    method: "POST",
    body: { token },
  });
}

export function authRequestPasswordReset(email: string) {
  return api<{ message: string }>("/auth/password-reset-request", {
    method: "POST",
    body: { email },
  });
}

export function authResetPassword(token: string, new_password: string) {
  return api<{ message: string }>("/auth/password-reset", {
    method: "POST",
    body: { token, new_password },
  });
}

export function authGoogle(id_token: string) {
  return api<TokenResponse>("/auth/google", {
    method: "POST",
    body: { id_token },
  });
}

export function getMe(token: string) {
  return api<UserResponse>("/auth/me", { token });
}
