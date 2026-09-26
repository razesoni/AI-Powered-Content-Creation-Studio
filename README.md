# AI-Powered Content Creation Studio

Implementation blueprint and starter scaffold derived from `AI_Powered_Content_Creation_Studio_SRS.pdf`.

## Start here

1. Read [`docs/01-project-structure.md`](docs/01-project-structure.md).
2. Follow [`docs/02-implementation-pipeline.md`](docs/02-implementation-pipeline.md).
3. Copy `.env.example` to `.env` and set at least `JWT_SECRET` and one AI key.
4. Run `docker compose up --build`.
5. Open the API at <http://localhost:8000/docs> and the web app at <http://localhost:5173>.

For a local Python environment on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Frontend dependencies are installed separately with `npm ci` from `frontend/`. The frontend connects to the local API by default; see [`frontend/README.md`](frontend/README.md) for the API contract and optional browser-only demo mode.

## Deliverables

- `docs/01-project-structure.md` - architecture, modules, folders, data flow, and database design
- `docs/02-implementation-pipeline.md` - phased build plan with acceptance checks
- `docs/03-api-and-ai-implementation.md` - API contracts, provider factory, prompts, safety, and observability
- `docs/04-resources.md` - official learning and implementation resources
- `docs/05-ai-tools-and-automation.md` - recommended LLMs and automation tools
- `docs/06-testing-deployment-security.md` - tests, CI/CD, deployment, and security checklist
- `docs/07-traceability-matrix.md` - SRS requirement mapping
- `database/001_initial_schema.sql` - pgAdmin-ready PostgreSQL schema
- `database/README.md` - database creation and backend connection steps
- `backend/`, `frontend/`, `infra/`, `.github/` - backend starter, complete frontend, and deployment scaffold

The frontend includes sign-in, project management, idea/outline/draft workflow, and a Markdown editor. It runs against a local demo data adapter until you set `VITE_DATA_MODE=api`. The backend remains a starter for your own implementation.
