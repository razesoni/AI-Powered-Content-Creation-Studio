# AI Tools and LLM Automation

Model names and prices change. Keep the selected model in environment configuration and verify the providers' model and pricing pages before deployment.

## Recommended runtime choices

| Need | Primary choice | Alternative | Implementation note |
|---|---|---|---|
| Ideas and outlines | A current low-latency OpenAI model with Structured Outputs | A current Gemini Flash-class model | Favor schema reliability and low cost |
| Long or nuanced drafts | A current higher-quality OpenAI model | A current Gemini Pro-class model | Offer as a quality mode after measuring cost |
| Local/private development | Ollama with a compatible open model | llama.cpp | Treat as a third adapter; test JSON adherence |
| Embeddings (future) | Provider embedding API | sentence-transformers | Needed only if adding semantic search/RAG |
| Moderation | Provider moderation endpoint and app rules | Perspective API for toxicity signals | Run before/after generation based on risk |

Avoid hard-coding a model name in business logic. Configure `OPENAI_MODEL`, `GEMINI_MODEL`, timeout, maximum output size, and per-user quotas.

## Development automation

| Tool | Use in this project |
|---|---|
| Codex or GitHub Copilot | scaffold code, explain failures, propose tests, and draft migrations under human review |
| Ruff + mypy | format/lint and statically check Python |
| ESLint + TypeScript | enforce frontend quality and type safety |
| OpenAPI TypeScript generator | regenerate typed frontend client from FastAPI schema |
| Dependabot or Renovate | dependency update pull requests |
| GitHub Actions | run checks, tests, image builds, security scans, and deployment gates |
| Trivy | container and dependency vulnerability scanning |
| pre-commit | run fast checks before code reaches CI |

## Content workflow automation

1. **Prompt assembly:** merge trusted template fields with validated project values.
2. **Schema generation:** derive provider JSON schema from Pydantic output models.
3. **Generation:** call the configured adapter with a request ID and timeout.
4. **Validation:** reject malformed, oversized, or semantically incomplete output.
5. **Persistence:** save only validated content and usage metadata.
6. **Evaluation:** score saved examples for schema validity, relevance, repetition, tone, and safety.
7. **Monitoring:** alert on latency/error/cost thresholds; do not log API keys or passwords.

## Evaluation rubric

Use a 1-5 human score for relevance, novelty, platform fit, tone match, organization, and edit effort. Add deterministic checks for exact item count, required headings, output length, duplicate titles, banned markup, and valid schema. Compare providers on the same frozen evaluation set and record model version, prompt version, temperature, latency, and token usage.

## Optional later additions

- Retrieval augmented generation from a user's approved brand guide and previous work.
- Background jobs with Celery/RQ and Redis once synchronous generation becomes a scaling problem.
- Server-Sent Events for generation progress.
- AI-assisted rewrite actions such as shorten, change tone, or create platform variants.
- Image/video generation only after the text MVP is stable; it is explicitly outside the SRS scope.
