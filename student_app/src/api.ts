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

export interface SearchResult {
  resource_id: string;
  title: string;
  course_id: string;
  category_slug: string;
  week_number?: number;
  score: number;
}

export const api = {
  // Discovery
  getInstitutions: async (): Promise<Institution[]> => {
    const res = await fetch(`${API_BASE}/api/v1/public/institutions`);
    return res.json();
  },
  getCourses: async (slug: string): Promise<Course[]> => {
    const res = await fetch(`${API_BASE}/api/v1/public/institutions/${slug}/courses`);
    return res.json();
  },
  getCategories: async (): Promise<MaterialCategory[]> => {
    const res = await fetch(`${API_BASE}/api/v1/public/categories`);
    return res.json();
  },

  // Search
  search: async (query: string): Promise<SearchResult[]> => {
    const res = await fetch(`${API_BASE}/api/v1/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const data = await res.json();
    return data.results;
  },

  // Identity / Auth
  loginWithTelegram: async (initData: string) => {
    const res = await fetch(`${API_BASE}/api/v1/auth/tma`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ init_data: initData })
    });
    if (!res.ok) throw new Error('Identity verification failed');
    return res.json();
  }
};
