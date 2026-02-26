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

export interface Question {
  id: string;
  order_index: number;
  question_text: string;
  question_type: string;
  probing_depth: number;
  help_text?: string | null;
  options_json?: string[] | null;
  scale_config?: Record<string, unknown> | null;
  branching_rules?: unknown;
  created_at: string | null;
  updated_at: string | null;
}

export async function fetchQuestions(
  token: string,
  projectId: string
): Promise<{ questions: Question[] }> {
  const r = await fetch(`${API_BASE}/api/v1/projects/${projectId}/questions`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) throw new Error(`Failed to fetch questions: ${r.status}`);
  return r.json();
}

export async function createQuestion(
  token: string,
  projectId: string,
  data: { question_text: string; question_type?: string; probing_depth?: number; help_text?: string }
): Promise<Question> {
  const r = await fetch(`${API_BASE}/api/v1/projects/${projectId}/questions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error(`Failed to create question: ${r.status}`);
  return r.json();
}

export async function updateQuestion(
  token: string,
  projectId: string,
  questionId: string,
  data: Partial<{
    question_text: string;
    question_type: string;
    probing_depth: number;
    help_text: string;
    options_json: string[];
    scale_config: Record<string, unknown>;
  }>
): Promise<Question> {
  const r = await fetch(`${API_BASE}/api/v1/projects/${projectId}/questions/${questionId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error(`Failed to update question: ${r.status}`);
  return r.json();
}

export async function reorderQuestions(
  token: string,
  projectId: string,
  questionId: string,
  newIndex: number
): Promise<{ questions: Question[] }> {
  const r = await fetch(`${API_BASE}/api/v1/projects/${projectId}/questions/reorder`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question_id: questionId, new_index: newIndex }),
  });
  if (!r.ok) throw new Error(`Failed to reorder: ${r.status}`);
  return r.json();
}

export async function deleteQuestion(
  token: string,
  projectId: string,
  questionId: string
): Promise<void> {
  const r = await fetch(`${API_BASE}/api/v1/projects/${projectId}/questions/${questionId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) throw new Error(`Failed to delete question: ${r.status}`);
}

export interface BatchQuestionPayload {
  order_index: number;
  question_text: string;
  question_type: string;
  probing_depth: number;
  help_text?: string;
  options_json?: string[] | { text: string; add_follow_up_branch?: boolean }[];
  scale_config?: Record<string, unknown>;
}

export async function batchPutQuestions(
  token: string,
  projectId: string,
  questions: BatchQuestionPayload[]
): Promise<{ questions: Question[] }> {
  const r = await fetch(`${API_BASE}/api/v1/projects/${projectId}/questions`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ questions }),
  });
  if (!r.ok) throw new Error(`Failed to save questions: ${r.status}`);
  return r.json();
}
