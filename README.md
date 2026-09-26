# AI-Powered Content Creation Studio

A starter scaffold and implementation blueprint for an AI-assisted content creation workflow. The project combines a React + TypeScript web app, a FastAPI backend, PostgreSQL persistence, and an AI provider abstraction for generating ideas, outlines, and drafts.

## Overview

This repository follows a three-tier architecture:

- React web app for the creator experience
- FastAPI application for routes, services, and business logic
- PostgreSQL for persistence and relational data model

The main user flow described in the project includes:

1. Register or sign in
2. Create a project with platform, content type, audience, and tone
3. Generate ideas
4. Select an idea and generate an outline
5. Generate a draft from the saved outline
6. Edit and save the draft with version tracking
7. Reopen the project and continue from any saved stage

## Stack

The project is intentionally structured around the following technologies:

- Web: React, TypeScript, Vite
- API: FastAPI, Pydantic, SQLAlchemy, Alembic
- Data: PostgreSQL
- Auth: JWT access tokens and Argon2 password hashing
- AI: provider interface with OpenAI and Gemini adapters
- Runtime: Docker Compose
- Delivery: GitHub Actions and Terraform

## Core Capabilities

- User authentication and authorization using JWT access tokens
- Project management with create, list, get, update, and delete flows
- AI-powered generation of content ideas, outlines, and drafts
- Structured persistence of generation metadata including provider, model, token usage, latency, and status
- Markdown draft editing and save flow with optimistic version checks
- Local Docker-based development environment and deployment scaffolding

## Project Structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- api/v1/
|   |   |-- core/
|   |   |-- db/
|   |   |-- models/
|   |   |-- schemas/
|   |   |-- repositories/
|   |   |-- services/
|   |   |-- ai/
|   |   `-- main.py
|   |-- tests/
|   |-- alembic/
|   |-- Dockerfile
|   `-- pyproject.toml
|-- frontend/
|   |-- src/
|   |   |-- api/
|   |   |-- components/
|   |   |-- features/
|   |   |-- pages/
|   |   |-- store/
|   |   `-- types/
|   |-- Dockerfile
|   `-- package.json
|-- infra/terraform/
|-- docs/
|-- .github/workflows/ci.yml
|-- compose.yaml
|-- .env.example
`-- README.md
```

## Getting Started

### 1) Configure environment variables

Copy the example environment file and set at least a `JWT_SECRET` and one AI provider key:

```bash
cp .env.example .env
```

### 2) Start the project

```bash
docker compose up --build
```

This starts the application stack together and provides:

- API documentation at `http://localhost:8000/docs`
- Web app at `http://localhost:5173`

### 3) Local Python environment

For a local Python setup on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4) Frontend setup

```bash
cd frontend
npm ci
npm run dev
```

## Documentation

The repository includes implementation documentation and planning artifacts:

- `docs/01-project-structure.md` — architecture, modules, data flow, and database design
- `docs/02-implementation-pipeline.md` — phased build plan and milestone checkpoints
- `docs/03-api-and-ai-implementation.md` — API contracts, provider factory, prompts, safety, and observability
- `docs/04-resources.md` — official learning and implementation resources
- `docs/05-ai-tools-and-automation.md` — recommended LLMs and automation tools
- `docs/06-testing-deployment-security.md` — tests, CI/CD, deployment, and security checklist
- `docs/07-traceability-matrix.md` — SRS requirement mapping

## Repository Deliverables

- Backend starter scaffold
- Complete frontend scaffold
- PostgreSQL schema definition and database guidance
- Infra and CI/CD scaffolding
- Implementation pipeline and project structure documentation

## Notes

- SQLite is used only for isolated unit tests.
- PostgreSQL remains the development and production source of truth.
- The project includes a Terraform implementation boundary for deployment modules and environment configuration.
- AI generation workflows are designed to include idempotency, validation, and status tracking.
