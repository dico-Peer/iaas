/** API base URL. In browser, use same origin when proxied; fallback for dev. */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Project {
  id: string;
  title: string;
  description: string | null;
  research_objectives: string | null;
  target_audience: string | null;
  language: string;
  modality: string;
  status: string;
  interview_count?: number;
  completion_pct?: number;
  cost?: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export async function fetchProjects(
  token: string,
  search?: string
): Promise<{ projects: Project[]; total: number }> {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  const url = `${API_BASE}/api/v1/projects${params.toString() ? `?${params}` : ""}`;
  const r = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) throw new Error(`Failed to fetch projects: ${r.status}`);
  return r.json();
}

export async function createProject(
  token: string,
  data: { title: string; description?: string; research_objectives?: string; target_audience?: string; language?: string; modality?: string }
): Promise<Project> {
  const r = await fetch(`${API_BASE}/api/v1/projects`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error(`Failed to create project: ${r.status}`);
  return r.json();
}
