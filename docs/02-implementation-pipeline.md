# Step-by-Step Implementation Pipeline

Each phase ends with a demonstrable checkpoint. Complete phases in order because later work depends on earlier contracts.

## Phase 0 - Foundation (day 1)

1. Install Docker Desktop, Git, and a current Node/Python toolchain for non-container work.
2. Copy `.env.example` to `.env`; create a long random `JWT_SECRET`; add one AI provider key.
3. Start `docker compose up --build` and verify `/health` returns `{"status":"ok"}`.
4. Initialize Git and protect the default branch with the CI workflow.

**Done when:** frontend, API, and PostgreSQL start together and no secret is committed.

## Phase 1 - Persistence and migrations (days 2-3)

1. Configure SQLAlchemy async engine and one session per request.
2. Implement the six entities in the ER specification with UUID keys, UTC timestamps, constraints, and cascades.
3. Configure Alembic; generate and review the initial migration.
4. Define repository protocols, then PostgreSQL implementations. Keep commits in the service layer when a use case writes multiple records.
5. Add test factories and a disposable test database.

**Done when:** a clean database upgrades to head and repository integration tests cover create, list, ownership filtering, and cascade deletion.

## Phase 2 - Authentication (days 4-5)

1. Add registration schemas and normalize email before checking uniqueness.
2. Hash passwords with Argon2; never log the submitted password.
3. Add login using OAuth2 password form or a documented JSON body.
4. Issue signed JWT access tokens containing `sub`, `iat`, `exp`, and a unique `jti`.
5. Add `get_current_user` dependency and apply it to every protected route.
6. Add profile GET/PATCH endpoints.

**Done when:** registration, login, invalid credentials, expired token, and duplicate email tests pass.

## Phase 3 - Project workspace (days 6-7)

1. Implement create, list, get, update, and delete project use cases.
2. Enforce ownership inside repositories/services, not only in route code.
3. Add pagination and stable ordering for lists.
4. Build login/register pages and a protected project dashboard.
5. Build project create/edit forms with shared client-side and server-side constraints.

**Done when:** user A cannot read, modify, generate under, or delete user B's project; browser CRUD flow succeeds.

## Phase 4 - AI abstraction (days 8-10)

1. Define `AIProvider.generate(schema, system_prompt, user_prompt)` and normalized usage metadata.
2. Implement `OpenAIProvider` with the Responses API and structured output.
3. Implement `GeminiProvider` with JSON schema output.
4. Implement `AIProviderFactory` selected by `AI_PROVIDER`; reject unknown values during startup.
5. Version prompts in code and keep provider parameters in configuration.
6. Add timeout, retry, refusal, malformed output, quota, and provider-unavailable mappings.

**Done when:** contract tests run against a fake provider, while optional smoke tests can run against either real provider.

## Phase 5 - Ideas, outlines, drafts (days 11-14)

1. Ideas: accept topic, platform, count, audience, and tone; return typed idea objects.
2. Outlines: require an owned saved idea; use platform templates for blog, long video, and short video.
3. Drafts: require an owned outline; request Markdown initially and sanitize rendered HTML in the browser.
4. Record provider, model, token counts, latency, outcome, and request ID in `ai_generations`.
5. Make generation idempotent and show loading, retry, and actionable failure states.

**Done when:** one automated E2E test completes Topic → Ideas → Outline → Draft and reloads persisted work.

## Phase 6 - Editor and usability (days 15-16)

1. Integrate TipTap or Lexical for rich text editing.
2. Autosave after a short idle delay and display saving/saved/error state.
3. Send the last known draft `version`; return `409` on a stale update.
4. Add keyboard navigation, labels, focus states, and responsive layouts.

**Done when:** edits survive reload, conflicting edits are detected, and core flows are keyboard usable.

## Phase 7 - Quality and security (days 17-18)

1. Add unit tests for services and prompt construction.
2. Add API integration tests for database constraints and authorization.
3. Add Playwright E2E coverage for the happy path and one provider failure.
4. Run Ruff, mypy, ESLint, TypeScript, tests, and production builds in CI.
5. Add rate limits to login and AI generation, strict CORS, security headers, request IDs, and structured logs.

**Done when:** CI is green from a clean clone and the checklist in `06-testing-deployment-security.md` passes.

## Phase 8 - Deployment and presentation (days 19-21)

1. Build immutable frontend and backend images tagged with commit SHA.
2. Provision network, managed PostgreSQL, secret injection, API runtime, frontend hosting, logs, and backups using Terraform modules.
3. Run migrations as a release step, then deploy API and frontend.
4. Configure HTTPS, health/readiness probes, database backups, and budget alerts.
5. Seed a demo account/project without real personal data and prepare the viva walkthrough.

**Done when:** production smoke tests pass, rollback is documented, and a fresh environment can be recreated from source plus secrets.

## Suggested milestone order

| Milestone | Output |
|---|---|
| M1 | Auth + database |
| M2 | Project CRUD + UI |
| M3 | One working provider + full generation flow |
| M4 | Second provider + editor + audit metrics |
| M5 | tests, CI, Terraform, deployed demonstration |
