const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

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

export interface MaterialCategory {
  slug: string;
  name: string;
  icon?: string;
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

export interface ResourceFilters {
  institutionSlug?: string;
  courseId?: string;
  categorySlug?: string;
  weekNumber?: number;
  limit?: number;
}

function buildQuery(filters?: ResourceFilters): string {
  if (!filters) {
    return '';
  }

  const params = new URLSearchParams();

  if (filters.institutionSlug) {
    params.set('institution_slug', filters.institutionSlug);
  }

  if (filters.courseId) {
    params.set('course_id', filters.courseId);
  }

  if (filters.categorySlug) {
    params.set('category_slug', filters.categorySlug);
  }

  if (typeof filters.weekNumber === 'number') {
    params.set('week_number', String(filters.weekNumber));
  }

  if (typeof filters.limit === 'number') {
    params.set('limit', String(filters.limit));
  }

  const query = params.toString();
  return query ? `?${query}` : '';
}

async function fetchJson<T>(input: string, init?: RequestInit): Promise<T> {
  const res = await fetch(input, init);
  if (!res.ok) {
    throw new Error(`Request failed with status ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export const api = {
  // Discovery
  getInstitutions: async (): Promise<Institution[]> => {
    return fetchJson<Institution[]>(`${API_BASE}/api/v1/public/institutions`);
  },
  getCourses: async (slug: string): Promise<Course[]> => {
    return fetchJson<Course[]>(`${API_BASE}/api/v1/public/institutions/${slug}/courses`);
  },
  getCategories: async (): Promise<MaterialCategory[]> => {
    return fetchJson<MaterialCategory[]>(`${API_BASE}/api/v1/public/categories`);
  },
  getResources: async (filters?: ResourceFilters): Promise<PublicResource[]> => {
    return fetchJson<PublicResource[]>(
      `${API_BASE}/api/v1/public/resources${buildQuery(filters)}`
    );
  },
  getCourseResources: async (
    courseId: string,
    filters?: Omit<ResourceFilters, 'courseId' | 'institutionSlug'>
  ): Promise<PublicResource[]> => {
    return fetchJson<PublicResource[]>(
      `${API_BASE}/api/v1/public/courses/${encodeURIComponent(courseId)}/resources${buildQuery(filters)}`
    );
  },

  // Search
  search: async (query: string, filters?: ResourceFilters): Promise<SearchResponse> => {
    return fetchJson<SearchResponse>(`${API_BASE}/api/v1/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        institution_slug: filters?.institutionSlug,
        course_id: filters?.courseId,
        category_slug: filters?.categorySlug,
        limit: filters?.limit,
      })
    });
  },

  // Identity / Auth
  loginWithTelegram: async (initData: string) => {
    return fetchJson(`${API_BASE}/api/v1/auth/tma`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ init_data: initData })
    });
  }
};
