# Studio frontend

A responsive React + TypeScript interface for the AI-Powered Content Creation Studio. The frontend can be explored without a backend in demo mode. Demo projects and generated examples are stored in browser local storage. They are illustrative content, not AI output.

## Run locally

```powershell
cd frontend
npm ci
npm run dev
```

Open <http://localhost:5173>. On the sign-in screen, choose **Explore the demo workspace**. You can create projects, generate sample ideas/outlines/drafts, edit and save drafts, preview Markdown, copy text, and download `.md` files.

## Connect your backend

Copy `.env.example` to `.env.local`, then set:

```env
VITE_DATA_MODE=api
VITE_API_URL=http://localhost:8000/api/v1
```

Restart Vite after changing environment variables. The frontend does not require you to edit page components to connect the API. Request code lives in `src/api/client.ts`; TypeScript response shapes live in `src/types.ts`.

If you use the root `docker compose` setup, set `VITE_DATA_MODE=api` in the root `.env` instead and restart the `web` service.

The browser sends a JSON login body and holds the access token in `sessionStorage`. Every protected request sends `Authorization: Bearer <token>`. Your backend must allow the frontend origin through CORS (`http://localhost:5173` for local development).

## Required endpoints

| Method | Path | Expected response |
|---|---|---|
| POST | `/auth/register` | User object |
| POST | `/auth/login` | `{ "access_token": "..." }` |
| GET | `/users/me` | User object |
| GET | `/projects?limit=100` | Project array or `{ "items": [...] }` |
| POST | `/projects` | Project object |
| DELETE | `/projects/:id` | `204` or success JSON |
| GET | `/projects/:id/ideas` | Idea array or `{ "items": [...] }` |
| POST | `/projects/:id/ideas/generate` | Idea array or `{ "ideas": [...] }` |
| GET | `/projects/:id/outlines` | Outline array or `{ "items": [...] }` |
| POST | `/projects/:id/outlines/generate` | Outline object |
| GET | `/projects/:id/drafts` | Draft array or `{ "items": [...] }` |
| POST | `/projects/:id/drafts/generate` | Draft object |
| PATCH | `/drafts/:id` | Updated Draft object |

List responses also accept `results` or `data` arrays. API paths and envelope normalization are centralized in `src/api/client.ts` if your backend uses another convention.

## Request and response examples

Create project:

```json
{
  "title": "Design Notes Weekly",
  "description": "Practical product design lessons",
  "platform": "LinkedIn",
  "content_type": "Article",
  "target_audience": "Designers and founders",
  "tone": "Thoughtful and clear"
}
```

Idea generation: `{ "topic": "creative habits", "count": 5, "instructions": "", "idempotency_key": "uuid" }`

Outline generation: `{ "idea_id": "uuid", "idempotency_key": "uuid" }`

Draft generation: `{ "outline_id": "uuid", "format": "markdown", "idempotency_key": "uuid" }`

Draft save: `{ "title": "...", "content": "# Markdown...", "version": 1 }`. Return the incremented version on success and `409` for a stale version.

Important response fields:

- `Project`: `id`, `title`, `description`, `platform`, `content_type`, `target_audience`, `tone`, `created_at`, `updated_at`
- `Idea`: `id`, `project_id`, `title`, `concept_summary`, `hook`, `platform`
- `Outline`: `id`, `project_id`, `idea_id`, `title`, `outline_data: { sections: [{ heading, purpose, key_points: string[] }], call_to_action? }`
- `Draft`: `id`, `project_id`, `outline_id`, `title`, `content` (Markdown), `format`, `version`, `updated_at`
- `User`: `id`, `full_name`, `email`

Return errors as `{ "code": "...", "message": "..." }` where possible. FastAPI's standard `detail` errors are also displayed. Use `404` for resources belonging to another user, so the UI cannot discover them.

## Build

```powershell
npm run build
npm run typecheck
```

The production assets are written to `dist/`. Google Fonts are used for presentation; system fonts are the fallback when offline.
