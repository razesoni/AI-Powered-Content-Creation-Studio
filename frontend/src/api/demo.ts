import type { Draft, DraftInput, Idea, IdeaInput, Outline, OutlineInput, Project, ProjectInput, StudioClient, User } from "../types";
import { newId } from "../utils/id";

type Data = { user: User | null; projects: Project[]; ideas: Idea[]; outlines: Outline[]; drafts: Draft[] };
const KEY = "content-studio-demo-v1";
const now = () => new Date().toISOString();
const uid = newId;
const pause = (ms = 350) => new Promise((resolve) => setTimeout(resolve, ms));
const seed: Data = {
  user: null,
  projects: [
    { id: "demo-1", title: "The Mindful Creator", description: "Ideas and scripts for a calmer creative life.", platform: "Instagram", content_type: "Post", target_audience: "Independent creators", tone: "Warm and encouraging", created_at: now(), updated_at: now() },
    { id: "demo-2", title: "Design Notes Weekly", description: "Practical lessons from the world of product design.", platform: "LinkedIn", content_type: "Article", target_audience: "Designers and founders", tone: "Thoughtful and clear", created_at: now(), updated_at: now() },
    { id: "demo-3", title: "Small Steps, Big Ideas", description: "Short educational videos about productive habits.", platform: "YouTube", content_type: "Video script", target_audience: "Students and young professionals", tone: "Friendly and energetic", created_at: now(), updated_at: now() },
  ], ideas: [], outlines: [], drafts: [],
};
function read(): Data {
  try { const value = localStorage.getItem(KEY); return value ? JSON.parse(value) as Data : structuredClone(seed); }
  catch { return structuredClone(seed); }
}
function write(data: Data) { localStorage.setItem(KEY, JSON.stringify(data)); }
function projectOrThrow(data: Data, id: string) {
  const project = data.projects.find((item) => item.id === id);
  if (!project) throw new Error("Project not found.");
  return project;
}

export const demoClient: StudioClient = {
  async login(email) { await pause(); const data = read(); data.user = { id: "demo-user", full_name: email.split("@")[0].replace(/[._-]/g, " ") || "Creator", email }; write(data); return data.user; },
  async register(fullName, email) { await pause(); const data = read(); data.user = { id: "demo-user", full_name: fullName, email }; write(data); return data.user; },
  logout() { const data = read(); data.user = null; write(data); },
  async currentUser() { return read().user; },
  async listProjects() { await pause(180); return read().projects.sort((a, b) => b.updated_at.localeCompare(a.updated_at)); },
  async createProject(input: ProjectInput) { await pause(); const data = read(); const project: Project = { ...input, id: uid(), created_at: now(), updated_at: now() }; data.projects.unshift(project); write(data); return project; },
  async deleteProject(id: string) { await pause(); const data = read(); data.projects = data.projects.filter((item) => item.id !== id); data.ideas = data.ideas.filter((item) => item.project_id !== id); data.outlines = data.outlines.filter((item) => item.project_id !== id); data.drafts = data.drafts.filter((item) => item.project_id !== id); write(data); },
  async listIdeas(projectId: string) { return read().ideas.filter((item) => item.project_id === projectId); },
  async generateIdeas(projectId: string, input: IdeaInput) {
    await pause(950); const data = read(); const project = projectOrThrow(data, projectId);
    const angles = [
      ["The beginner's guide to", "A clear, approachable introduction that removes the overwhelm.", "What if getting started was simpler than you think?"],
      ["What nobody tells you about", "An honest look at the lessons people usually learn too late.", "I wish someone had told me this sooner."],
      ["5 small shifts for", "Practical ideas your audience can try right away.", "Big progress often starts with one tiny change."],
      ["A fresh perspective on", "A distinctive angle that challenges a common assumption.", "Maybe we've been looking at this the wrong way."],
      ["From idea to action:", "A useful framework that turns inspiration into a plan.", "Here's a simple way to actually begin."],
      ["The overlooked side of", "A thoughtful take on a topic your audience already cares about.", "There's one part of this conversation we're missing."],
      ["How to make progress with", "A realistic, step-by-step idea for busy people.", "You don't need a perfect plan to make progress."],
      ["A better way to think about", "A reframing that creates a memorable insight.", "What changes when you ask a different question?"],
      ["The simple checklist for", "A save-worthy practical resource for your audience.", "Save this for the next time you need it."],
      ["One lesson I learned about", "A personal-story format with a useful takeaway.", "This changed how I approach the whole thing."],
    ];
    const ideas = angles.slice(0, input.count).map(([prefix, summary, hook]) => ({ id: uid(), project_id: projectId, title: `${prefix} ${input.topic.trim()}`, concept_summary: summary, hook, platform: project.platform, created_at: now() }));
    data.ideas.push(...ideas); project.updated_at = now(); write(data); return ideas;
  },
  async listOutlines(projectId: string) { return read().outlines.filter((item) => item.project_id === projectId); },
  async generateOutline(projectId: string, input: OutlineInput) {
    await pause(850); const data = read(); projectOrThrow(data, projectId); const idea = data.ideas.find((item) => item.id === input.idea_id && item.project_id === projectId); if (!idea) throw new Error("Choose an idea first.");
    const outline: Outline = { id: uid(), project_id: projectId, idea_id: idea.id, title: idea.title, outline_data: { sections: [
      { heading: "The hook", purpose: "Grab attention and establish a reason to keep reading.", key_points: [idea.hook, "Lead with a relatable moment or question."] },
      { heading: "The core insight", purpose: "Explain the central idea in plain language.", key_points: [idea.concept_summary, "Make the takeaway specific and memorable."] },
      { heading: "Make it practical", purpose: "Give your audience something they can use today.", key_points: ["Share two or three concrete steps.", "Include a realistic example."] },
      { heading: "The close", purpose: "Leave the audience with a clear next step.", key_points: ["Recap the most useful point.", "Invite a thoughtful response."] },
    ], call_to_action: "What would you try first? Share your take in the comments." }, created_at: now() };
    data.outlines.push(outline); write(data); return outline;
  },
  async listDrafts(projectId: string) { return read().drafts.filter((item) => item.project_id === projectId); },
  async generateDraft(projectId: string, input: DraftInput) {
    await pause(900); const data = read(); const project = projectOrThrow(data, projectId); const outline = data.outlines.find((item) => item.id === input.outline_id && item.project_id === projectId); if (!outline) throw new Error("Create an outline first.");
    const content = `# ${outline.title}\n\n${outline.outline_data.sections.map((section) => `## ${section.heading}\n\n${section.purpose} ${section.key_points.join(" ")}`).join("\n\n")}\n\n${outline.outline_data.call_to_action || ""}`;
    const draft: Draft = { id: uid(), project_id: projectId, outline_id: outline.id, title: outline.title, content, format: input.format, version: 1, updated_at: now() };
    data.drafts.push(draft); project.updated_at = now(); write(data); return draft;
  },
  async saveDraft(id: string, input: Pick<Draft, "title" | "content" | "version">) {
    await pause(300); const data = read(); const draft = data.drafts.find((item) => item.id === id); if (!draft) throw new Error("Draft not found.");
    if (input.version !== draft.version) throw new Error("This draft changed elsewhere. Reload before saving.");
    Object.assign(draft, { title: input.title, content: input.content, version: draft.version + 1, updated_at: now() }); write(data); return { ...draft };
  },
};
