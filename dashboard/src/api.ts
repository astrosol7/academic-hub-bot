const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export type ApiError = { status: number; detail: string };

function getAccessToken(): string | null {
  return localStorage.getItem('orbit_access_token');
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as any),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const resp = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  const contentType = resp.headers.get('content-type') || '';
  const body = contentType.includes('application/json') ? await resp.json() : await resp.text();

  if (!resp.ok) {
    const detail = typeof body === 'object' && body?.detail ? body.detail : `HTTP ${resp.status}`;
    throw { status: resp.status, detail } as ApiError;
  }
  return body as T;
}

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

export type IncidentStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'REJECTED';

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

export type TelemetryRow = { query: string; count: number };

export type QuarantineStatus = 'PENDING' | 'RECOVERED' | 'IGNORED';
export type QuarantineItem = {
  id: string;
  file_path: string;
  reason: string;
  status: QuarantineStatus;
  detected_at: string;
};

export const api = {
  overview: () => apiFetch<Overview>('/api/v1/admin/overview?institution_slug=sit'),
  incidents: () => apiFetch<Incident[]>('/api/v1/admin/incidents?limit=100'),
  updateIncident: (id: string, status: IncidentStatus, resolution_note?: string) =>
    apiFetch<Incident>(`/api/v1/admin/incidents/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status, resolution_note: resolution_note || null }),
    }),
  students: (q?: string) =>
    apiFetch<StudentRow[]>(
      `/api/v1/admin/students?institution_slug=sit&limit=200${q ? `&q=${encodeURIComponent(q)}` : ''}`
    ),
  unbind: (telegram_id?: string, school_id?: string) =>
    apiFetch<{ status: string; count: number }>('/api/v1/admin/links/unbind', {
      method: 'POST',
      body: JSON.stringify({ institution_slug: 'sit', telegram_id: telegram_id || null, school_id: school_id || null }),
    }),
  telemetryTop: () => apiFetch<TelemetryRow[]>('/api/v1/admin/telemetry/top-queries?limit=20'),
  telemetryFailed: () => apiFetch<TelemetryRow[]>('/api/v1/admin/telemetry/failed-queries?limit=20'),
  quarantine: () => apiFetch<QuarantineItem[]>('/api/v1/admin/quarantine?status=PENDING&limit=200'),
  updateQuarantine: (id: string, status: QuarantineStatus) =>
    apiFetch<{ status: string }>(`/api/v1/admin/quarantine/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),
};

