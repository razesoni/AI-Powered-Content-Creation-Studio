export type Platform = "Instagram" | "YouTube" | "LinkedIn" | "TikTok" | "Blog";
export type ContentType = "Post" | "Article" | "Video script" | "Short video";
export interface User { id: string; full_name: string; email: string }
export interface Project {
  id: string; title: string; description: string; platform: Platform; content_type: ContentType;
  target_audience: string; tone: string; created_at: string; updated_at: string;
}
export type ProjectInput = Pick<Project, "title" | "description" | "platform" | "content_type" | "target_audience" | "tone">;
export interface Idea {
  id: string; project_id: string; title: string; concept_summary: string; hook: string; platform: string; created_at?: string;
}
export interface OutlineSection { heading: string; purpose: string; key_points: string[] }
export interface Outline {
  id: string; project_id: string; idea_id: string; title: string;
  outline_data: { sections: OutlineSection[]; call_to_action?: string }; created_at?: string;
}
export interface Draft {
  id: string; project_id: string; outline_id: string; title: string; content: string;
  format: string; version: number; updated_at: string;
}
export interface IdeaInput { topic: string; count: number; instructions?: string; idempotency_key: string }
export interface OutlineInput { idea_id: string; instructions?: string; idempotency_key: string }
export interface DraftInput { outline_id: string; format: string; instructions?: string; idempotency_key: string }
export interface StudioClient {
  login(email: string, password: string): Promise<User>;
  register(fullName: string, email: string, password: string): Promise<User>;
  logout(): void;
  currentUser(): Promise<User | null>;
  listProjects(): Promise<Project[]>;
  createProject(input: ProjectInput): Promise<Project>;
  deleteProject(id: string): Promise<void>;
  listIdeas(projectId: string): Promise<Idea[]>;
  generateIdeas(projectId: string, input: IdeaInput): Promise<Idea[]>;
  listOutlines(projectId: string): Promise<Outline[]>;
  generateOutline(projectId: string, input: OutlineInput): Promise<Outline>;
  listDrafts(projectId: string): Promise<Draft[]>;
  generateDraft(projectId: string, input: DraftInput): Promise<Draft>;
  saveDraft(id: string, input: Pick<Draft, "title" | "content" | "version">): Promise<Draft>;
}
