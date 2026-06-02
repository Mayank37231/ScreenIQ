export type Application = {
  id: number;
  job_description: string;
  resume: string;
  candidate_name: string;
  ai_score: string;
  ai_reasons: string[];
  created_at: string;
};

export type ApplicationPage = {
  count: number;
  limit: number;
  offset: number;
  results: Application[];
};

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export function getToken() {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem("screeniq_token") || "";
}

export function setToken(token: string) {
  window.localStorage.setItem("screeniq_token", token);
}

export function scoreClass(score: string | number) {
  const value = Number(score);
  if (Number.isNaN(value) || value < 5) return "red";
  if (value <= 7) return "amber";
  return "green";
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers
    }
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }

  return response.json();
}
