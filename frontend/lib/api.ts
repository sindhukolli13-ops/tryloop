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

// ── Device types ──

export interface DeviceResponse {
  id: number;
  name: string;
  brand: string;
  category: string;
  description: string | null;
  specs: Record<string, string> | null;
  images: string[] | null;
  trial_price_7d: number;
  trial_price_14d: number;
  purchase_price: number;
  deposit_amount: number;
  is_featured: boolean;
  is_active: boolean;
  available_units: number;
  created_at: string;
  updated_at: string;
}

export interface DeviceListResponse {
  items: DeviceResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface DeviceCompareResponse {
  devices: DeviceResponse[];
}

export interface FilterOptions {
  categories: string[];
  brands: string[];
}

// ── Device query params ──

export interface DeviceListParams {
  page?: number;
  page_size?: number;
  category?: string;
  brand?: string;
  search?: string;
  min_price?: number;
  max_price?: number;
  is_featured?: boolean;
  available_only?: boolean;
}

// ── Typed device endpoints ──

export function getDevices(params: DeviceListParams = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.append(key, String(value));
    }
  });
  const qs = searchParams.toString();
  return api<DeviceListResponse>(`/devices${qs ? `?${qs}` : ""}`);
}

export function getDevice(id: number) {
  return api<DeviceResponse>(`/devices/${id}`);
}

export function getFeaturedDevices(limit = 6) {
  return api<DeviceResponse[]>(`/devices/featured?limit=${limit}`);
}

export function getFilterOptions() {
  return api<FilterOptions>("/devices/filters");
}

export function compareDevices(ids: number[]) {
  const qs = ids.map((id) => `ids=${id}`).join("&");
  return api<DeviceCompareResponse>(`/devices/compare?${qs}`);
}

// ── Trial types ──

export interface TrialResponse {
  id: number;
  user_id: number;
  device_id: number;
  device_unit_id: number;
  duration_days: number;
  start_date: string | null;
  end_date: string | null;
  status: string;
  trial_fee: number;
  deposit_amount: number;
  stripe_payment_intent_id: string | null;
  created_at: string;
  updated_at: string;
  device_name: string | null;
  device_brand: string | null;
  device_image: string | null;
}

export interface TrialListResponse {
  items: TrialResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface CheckoutSessionResponse {
  checkout_url: string;
  session_id: string;
  trial_id: number;
}

// ── Typed trial endpoints ──

export function createTrialCheckout(
  data: { device_id: number; duration_days: number },
  token: string
) {
  return api<CheckoutSessionResponse>("/trials/checkout", {
    method: "POST",
    body: data,
    token,
  });
}

export function getMyTrials(
  token: string,
  params: { page?: number; page_size?: number; status?: string } = {}
) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  });
  const qs = searchParams.toString();
  return api<TrialListResponse>(`/trials/my${qs ? `?${qs}` : ""}`, { token });
}

export function getMyTrial(trialId: number, token: string) {
  return api<TrialResponse>(`/trials/my/${trialId}`, { token });
}

export function cancelMyTrial(trialId: number, token: string) {
  return api<TrialResponse>(`/trials/my/${trialId}/cancel`, {
    method: "POST",
    token,
  });
}

// ── Device Unit types ──

export interface DeviceUnitResponse {
  id: number;
  device_id: number;
  serial_number: string;
  condition_grade: string;
  status: string;
  rental_count: number;
  total_lifecycle_revenue: number;
  created_at: string;
  updated_at: string;
}

export interface DeviceUnitListResponse {
  items: DeviceUnitResponse[];
  total: number;
  page: number;
  page_size: number;
}

// ── Admin device endpoints ──

export function adminCreateDevice(
  data: {
    name: string;
    brand: string;
    category: string;
    description?: string;
    specs?: Record<string, string>;
    images?: string[];
    trial_price_7d: number;
    trial_price_14d: number;
    purchase_price: number;
    deposit_amount: number;
    is_featured?: boolean;
    is_active?: boolean;
  },
  token: string
) {
  return api<DeviceResponse>("/devices", { method: "POST", body: data, token });
}

export function adminUpdateDevice(
  id: number,
  data: Partial<{
    name: string;
    brand: string;
    category: string;
    description: string;
    specs: Record<string, string>;
    images: string[];
    trial_price_7d: number;
    trial_price_14d: number;
    purchase_price: number;
    deposit_amount: number;
    is_featured: boolean;
    is_active: boolean;
  }>,
  token: string
) {
  return api<DeviceResponse>(`/devices/${id}`, {
    method: "PATCH",
    body: data,
    token,
  });
}

export function adminDeleteDevice(id: number, token: string) {
  return api<{ message: string }>(`/devices/${id}`, {
    method: "DELETE",
    token,
  });
}

// ── Admin inventory (unit) endpoints ──

export function adminGetUnits(
  token: string,
  params: {
    page?: number;
    page_size?: number;
    device_id?: number;
    status?: string;
    condition_grade?: string;
  } = {}
) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  });
  const qs = searchParams.toString();
  return api<DeviceUnitListResponse>(
    `/inventory/units${qs ? `?${qs}` : ""}`,
    { token }
  );
}

export function adminGetUnit(unitId: number, token: string) {
  return api<DeviceUnitResponse>(`/inventory/units/${unitId}`, { token });
}

export function adminCreateUnit(
  data: { device_id: number; serial_number: string; condition_grade?: string },
  token: string
) {
  return api<DeviceUnitResponse>("/inventory/units", {
    method: "POST",
    body: data,
    token,
  });
}

export function adminUpdateUnit(
  unitId: number,
  data: { serial_number?: string; condition_grade?: string; status?: string },
  token: string
) {
  return api<DeviceUnitResponse>(`/inventory/units/${unitId}`, {
    method: "PATCH",
    body: data,
    token,
  });
}

export function adminDeleteUnit(unitId: number, token: string) {
  return api<{ message: string }>(`/inventory/units/${unitId}`, {
    method: "DELETE",
    token,
  });
}

export function adminGetUnitStatusCounts(
  deviceId: number,
  token: string
) {
  return api<Record<string, number>>(
    `/inventory/units/device/${deviceId}/status-counts`,
    { token }
  );
}
