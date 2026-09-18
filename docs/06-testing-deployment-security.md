# Testing, Deployment, and Security

## Test pyramid

### Unit tests

- services with fake repositories and a fake AI provider
- password/JWT boundary cases
- prompt construction and platform template selection
- schema validation and provider error mapping

### Integration tests

- real PostgreSQL migrations and repository queries
- registration/login and duplicate email
- project CRUD and cascade deletion
- cross-user access for every resource endpoint
- idempotent generation and failed-generation audit records
- stale draft version produces `409`

### End-to-end tests

- register → create project → generate ideas → outline → draft → edit → reload
- AI timeout followed by a successful retry
- logout and expired-session handling

Do not call paid AI APIs in ordinary CI. Use a deterministic fake and run a small real-provider smoke suite manually or on a budgeted schedule.

## CI/CD stages

1. Checkout and restore dependency caches.
2. Backend lint/type check, migration check, and tests.
3. Frontend lint/type check, component tests, and production build.
4. Build containers and scan them.
5. On the protected release branch, push images tagged by commit SHA.
6. Run Terraform plan for review.
7. After approval, apply infrastructure, run database migrations, deploy, and execute smoke tests.
8. Roll back to the prior image if readiness or smoke checks fail.

## Deployment topology

- Static frontend on a CDN/object store.
- API in a managed container service with at least two instances when availability matters.
- Managed PostgreSQL in private networking with encrypted connections and automated backups.
- Secrets in the cloud secret manager, injected at runtime.
- Central logs and metrics with request IDs shared across frontend error reports, API logs, and AI audit rows.

The `infra/terraform` folder contains provider-neutral module boundaries because a real Terraform implementation requires a selected cloud, region, account, domain, and budget.

## Security checklist

- [ ] Argon2id hashes with reviewed parameters; generic login failure messages.
- [ ] Strong JWT secret/key, short access-token lifetime, issuer/audience validation, and clock-skew limit.
- [ ] Ownership-scoped queries for projects, ideas, outlines, drafts, and generations.
- [ ] CORS allowlist contains only deployed frontend origins.
- [ ] Login and generation rate limits; request body and output size limits.
- [ ] Provider keys and database credentials exist only in environment/secret manager.
- [ ] TLS everywhere outside local development.
- [ ] Markdown/HTML sanitized before browser rendering; Content Security Policy enabled.
- [ ] Dependency and image scanning in CI.
- [ ] Database backups tested with a restore drill.
- [ ] Logs exclude passwords, tokens, API keys, and raw sensitive prompts.
- [ ] Account/project deletion behavior and audit retention documented.

## Performance targets

- Measure non-AI endpoint p95 below 500 ms using a production-like database.
- Track AI latency separately; the SRS target is 5-20 seconds.
- Add query-count checks to list/detail views, paginate lists, and index ownership paths.
- Load test login, project list, save draft, and generation admission controls; do not load test paid providers without a fixed budget.
