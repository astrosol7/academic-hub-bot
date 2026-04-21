const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const ACCESS_TOKEN_KEY = "orbit_access_token";
const REFRESH_TOKEN_KEY = "orbit_refresh_token";
const API_BASE_KEY = "orbit_api_base_url";

export const AUTH_EXPIRED_EVENT = "orbit:auth-expired";

export type ApiError = { status: number; detail: string };

export type HealthResponse = {
  status: string;
  version: string;
  release: string;
  setup_required: boolean;
};

export type Overview = {
  institution_slug: string;
  students_total: number;
  links_total: number;
  conflicts_total: number;
  incidents_open: number;
  incidents_in_progress: number;
  incidents_resolved: number;
  quarantine_pending: number;
};

export type IncidentStatus = "OPEN" | "IN_PROGRESS" | "RESOLVED" | "REJECTED";

export type Incident = {
  id: string;
  telegram_id: string;
  category: string;
  description: string;
  course_id?: string | null;
  status: IncidentStatus;
  created_at: string;
  updated_at: string;
  resolution_note?: string | null;
};

export type StudentRow = {
  student_id: string;
  full_name: string;
  telegram_id?: string | null;
  is_conflicted: boolean;
};

export type TelemetryRow = {
  query: string;
  count: number;
};

export type QuarantineStatus = "PENDING" | "RECOVERED" | "IGNORED";

export type QuarantineItem = {
  id: string;
  file_path: string;
  reason: string;
  severity?: string | null;
  status: QuarantineStatus;
  detected_at: string;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

function normalizeStoredBase(url: string): string {
  return url.replace(/\/+$/, "");
}

export function normalizeApiBaseUrl(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    return DEFAULT_API_BASE_URL;
  }

  const withProtocol = /^https?:\/\//i.test(trimmed) ? trimmed : `http://${trimmed}`;
  return normalizeStoredBase(withProtocol);
}

export function getConfiguredApiBaseUrl(): string {
  const stored = typeof window !== "undefined" ? window.localStorage.getItem(API_BASE_KEY) : null;
  if (stored && stored.trim()) {
    return normalizeApiBaseUrl(stored);
  }

  const envBase = import.meta.env?.VITE_API_BASE_URL;
  return normalizeApiBaseUrl(envBase || DEFAULT_API_BASE_URL);
}

export function setConfiguredApiBaseUrl(url: string): string {
  const normalized = normalizeApiBaseUrl(url);
  window.localStorage.setItem(API_BASE_KEY, normalized);
  return normalized;
}

export function clearStoredSession(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

function getAccessToken(): string | null {
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken(): string | null {
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

function setAccessToken(token: string): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

function dispatchAuthExpired(): void {
  clearStoredSession();
  window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT));
}

function buildHeaders(initHeaders?: HeadersInit, includeJson = true): Headers {
  const headers = new Headers(initHeaders);
  if (includeJson && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = getAccessToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return headers;
}

async function parseResponseBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function asApiError(status: number, body: unknown): ApiError {
  if (body && typeof body === "object" && "detail" in body && typeof body.detail === "string") {
    return { status, detail: body.detail };
  }
  if (typeof body === "string" && body.trim()) {
    return { status, detail: body };
  }
  return { status, detail: `HTTP ${status}` };
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    dispatchAuthExpired();
    return null;
  }

  const response = await fetch(`${getConfiguredApiBaseUrl()}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    dispatchAuthExpired();
    return null;
  }

  const body = (await response.json()) as TokenResponse;
  setAccessToken(body.access_token);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, body.refresh_token);
  return body.access_token;
}

async function apiFetch<T>(path: string, init: RequestInit = {}, retryOnAuth = true): Promise<T> {
  const includeJson = !(init.body instanceof FormData);
  const response = await fetch(`${getConfiguredApiBaseUrl()}${path}`, {
    ...init,
    headers: buildHeaders(init.headers, includeJson),
  });

  const body = await parseResponseBody(response);

  if (!response.ok) {
    if (response.status === 401 && retryOnAuth) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        return apiFetch<T>(path, init, false);
      }
    }

    const error = asApiError(response.status, body);
    if (error.status === 401) {
      dispatchAuthExpired();
    }
    throw error;
  }

  return body as T;
}

async function unauthenticatedJsonFetch<T>(
  path: string,
  init: RequestInit = {},
  apiBaseUrl?: string,
): Promise<T> {
  const response = await fetch(`${normalizeApiBaseUrl(apiBaseUrl || getConfiguredApiBaseUrl())}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {}),
    },
  });

  const body = await parseResponseBody(response);
  if (!response.ok) {
    throw asApiError(response.status, body);
  }
  return body as T;
}

export interface PublicResource {
  id: string;
  title: string;
  course_id: string;
  course_title: string;
  institution_slug: string;
  institution_name: string;
  category_slug: string;
  category_name: string;
  week_number?: number;
  topic_group?: string;
  tags: string[];
  source_type: string;
  created_at: string;
  access_url?: string | null;
  available_in_web: boolean;
}

export interface SearchResult {
  resource_id: string;
  title: string;
  course_id: string;
  course_title: string;
  institution_slug: string;
  institution_name: string;
  category_slug: string;
  category_name: string;
  week_number?: number;
  topic_group?: string;
  tags: string[];
  score: number;
  kind?: string;
  source_type: string;
  created_at?: string;
  access_url?: string | null;
  available_in_web: boolean;
}

export interface SearchResponse {
  results: SearchResult[];
  engine: string;
  suggestions: string[];
}

export interface Institution {
  id: string;
  slug: string;
  name: string;
}

export interface Course {
  id: string;
  title: string;
  week_count?: number;
}

export const api = {
  health: (apiBaseUrl?: string) =>
    unauthenticatedJsonFetch<HealthResponse>("/api/v1/health", { method: "GET" }, apiBaseUrl),

  login: (username: string, password: string, apiBaseUrl?: string) =>
    unauthenticatedJsonFetch<TokenResponse>(
      "/api/v1/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ username, password }),
      },
      apiBaseUrl,
    ),

  bootstrap: (username: string, password: string, apiBaseUrl?: string) =>
    unauthenticatedJsonFetch<TokenResponse>(
      "/api/v1/auth/bootstrap",
      {
        method: "POST",
        body: JSON.stringify({ username, password }),
      },
      apiBaseUrl,
    ),

  overview: () => apiFetch<Overview>("/api/v1/admin/overview?institution_slug=sit"),

  incidents: () => apiFetch<Incident[]>("/api/v1/admin/incidents?limit=500"),

  updateIncident: (id: string, status: IncidentStatus, resolution_note?: string) =>
    apiFetch<Incident>(`/api/v1/admin/incidents/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status, resolution_note: resolution_note || null }),
    }),

  students: (q?: string) =>
    apiFetch<StudentRow[]>(
      `/api/v1/admin/students?institution_slug=sit&limit=2000${q ? `&q=${encodeURIComponent(q)}` : ""}`,
    ),

  unbind: (school_id: string, telegram_id?: string) =>
    apiFetch<{ status: string; count: number }>("/api/v1/admin/links/unbind", {
      method: "POST",
      body: JSON.stringify({
        institution_slug: "sit",
        school_id,
        telegram_id: telegram_id || null,
      }),
    }),

  telemetryTop: () => apiFetch<TelemetryRow[]>("/api/v1/admin/telemetry/top-queries?limit=20"),

  telemetryFailed: () => apiFetch<TelemetryRow[]>("/api/v1/admin/telemetry/failed-queries?limit=20"),

  quarantine: () => apiFetch<QuarantineItem[]>("/api/v1/admin/quarantine?status=PENDING&limit=200"),

  updateQuarantine: (id: string, status: QuarantineStatus) =>
    apiFetch<{ status: string }>(`/api/v1/admin/quarantine/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  // Voyager (Student) Methods
  getInstitutions: async (): Promise<Institution[]> => {
    return unauthenticatedJsonFetch<Institution[]>("/api/v1/public/institutions");
  },

  getCourses: async (slug: string): Promise<Course[]> => {
    return unauthenticatedJsonFetch<Course[]>(`/api/v1/public/institutions/${slug}/courses`);
  },

  search: async (query: string, filters?: any): Promise<SearchResponse> => {
    return unauthenticatedJsonFetch<SearchResponse>("/api/v1/search", {
      method: "POST",
      body: JSON.stringify({
        query,
        institution_slug: filters?.institutionSlug,
        course_id: filters?.courseId,
        category_slug: filters?.categorySlug,
        limit: filters?.limit,
      }),
    });
  },

  loginWithTelegram: async (initData: string) => {
    return unauthenticatedJsonFetch<TokenResponse>("/api/v1/auth/tma", {
      method: "POST",
      body: JSON.stringify({ init_data: initData }),
    });
  },
};
