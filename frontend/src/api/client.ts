import type { Draft, DraftInput, Idea, IdeaInput, Outline, OutlineInput, Project, ProjectInput, StudioClient, User } from "../types";

const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");
const TOKEN_KEY = "content-studio-token";

export class ApiError extends Error {
  constructor(message: string, public status: number, public code?: string) { super(message); }
}

function asList<T>(value: unknown, key: string): T[] {
  if (Array.isArray(value)) return value as T[];
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    for (const candidate of [key, "items", "results", "data"]) {
      if (Array.isArray(record[candidate])) return record[candidate] as T[];
    }
  }
  throw new Error(`Unexpected ${key} response. Check the backend response shape.`);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = sessionStorage.getItem(TOKEN_KEY);
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new ApiError("Cannot reach the API. Check VITE_API_URL and that your backend is running.", 0, "network_error");
  }
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.message || data.detail || `Request failed (${response.status})`;
    throw new ApiError(typeof message === "string" ? message : JSON.stringify(message), response.status, data.code);
  }
  return data as T;
}

const body = (data: unknown) => JSON.stringify(data);

export const apiClient: StudioClient = {
  async login(email, password) {
    const result = await request<{ access_token: string }>("/auth/login", { method: "POST", body: body({ email, password }) });
    sessionStorage.setItem(TOKEN_KEY, result.access_token);
    return request<User>("/users/me");
  },
  async register(fullName, email, password) {
    await request<User>("/auth/register", { method: "POST", body: body({ full_name: fullName, email, password }) });
    return this.login(email, password);
  },
  logout() { sessionStorage.removeItem(TOKEN_KEY); },
  async currentUser() {
    if (!sessionStorage.getItem(TOKEN_KEY)) return null;
    try { return await request<User>("/users/me"); }
    catch (error) { if (error instanceof ApiError && error.status === 401) sessionStorage.removeItem(TOKEN_KEY); return null; }
  },
  async listProjects() { return asList<Project>(await request("/projects?limit=100"), "projects"); },
  createProject(input: ProjectInput) { return request<Project>("/projects", { method: "POST", body: body(input) }); },
  deleteProject(id: string) { return request<void>(`/projects/${encodeURIComponent(id)}`, { method: "DELETE" }); },
  async listIdeas(projectId: string) { return asList<Idea>(await request(`/projects/${encodeURIComponent(projectId)}/ideas`), "ideas"); },
  async generateIdeas(projectId: string, input: IdeaInput) { return asList<Idea>(await request(`/projects/${encodeURIComponent(projectId)}/ideas/generate`, { method: "POST", body: body(input) }), "ideas"); },
  async listOutlines(projectId: string) { return asList<Outline>(await request(`/projects/${encodeURIComponent(projectId)}/outlines`), "outlines"); },
  generateOutline(projectId: string, input: OutlineInput) { return request<Outline>(`/projects/${encodeURIComponent(projectId)}/outlines/generate`, { method: "POST", body: body(input) }); },
  async listDrafts(projectId: string) { return asList<Draft>(await request(`/projects/${encodeURIComponent(projectId)}/drafts`), "drafts"); },
  generateDraft(projectId: string, input: DraftInput) { return request<Draft>(`/projects/${encodeURIComponent(projectId)}/drafts/generate`, { method: "POST", body: body(input) }); },
  saveDraft(id: string, input: Pick<Draft, "title" | "content" | "version">) { return request<Draft>(`/drafts/${encodeURIComponent(id)}`, { method: "PATCH", body: body(input) }); },
};
