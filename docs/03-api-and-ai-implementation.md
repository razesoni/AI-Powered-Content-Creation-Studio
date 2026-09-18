# API and AI Implementation

## API contract

All routes are prefixed `/api/v1`. Protected requests use `Authorization: Bearer <token>`.

| Method and path | Request | Success |
|---|---|---|
| `POST /auth/register` | full_name, email, password | `201 User` |
| `POST /auth/login` | email, password | `200 Token` |
| `GET /users/me` | - | `200 User` |
| `PATCH /users/me` | full_name | `200 User` |
| `GET /projects?cursor=&limit=` | - | `200 Page[Project]` |
| `POST /projects` | title, description, platform, content_type, audience, tone | `201 Project` |
| `GET/PATCH/DELETE /projects/{id}` | endpoint-specific | `200/204` |
| `POST /projects/{id}/ideas/generate` | topic, count, optional instructions, idempotency_key | `201 Idea[]` |
| `POST /projects/{id}/outlines/generate` | idea_id, optional instructions, idempotency_key | `201 Outline` |
| `POST /projects/{id}/drafts/generate` | outline_id, format, optional instructions, idempotency_key | `201 Draft` |
| `GET /projects/{id}/drafts` | - | `200 Draft[]` |
| `PATCH /drafts/{id}` | title, content, version | `200 Draft` or `409` |

Use `400` for invalid workflow state, `401` for missing/invalid authentication, `403` only when revealing existence is safe, `404` for inaccessible user resources, `409` for uniqueness/version conflicts, `422` for schema errors, `429` for rate limits, and `502/503/504` for provider failures.

## Internal provider contract

```python
class AIProvider(Protocol):
    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        request_id: str,
    ) -> GenerationResult: ...

class GenerationResult(BaseModel):
    data: BaseModel
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
```

`AIProviderFactory.create(settings)` returns the OpenAI or Gemini adapter. Services depend on the protocol, so tests inject `FakeAIProvider` with deterministic responses.

## Structured schemas

```python
class ContentIdea(BaseModel):
    title: str
    concept_summary: str
    hook: str
    platform: str

class IdeaBatch(BaseModel):
    ideas: list[ContentIdea]

class OutlineSection(BaseModel):
    heading: str
    purpose: str
    key_points: list[str]

class GeneratedOutline(BaseModel):
    title: str
    sections: list[OutlineSection]
    call_to_action: str | None = None

class GeneratedDraft(BaseModel):
    title: str
    content_markdown: str
```

Apply application-level limits after parsing: exact requested idea count, title/field lengths, maximum sections, and maximum draft size.

## Prompt design

Each prompt has four blocks: role, project context, task, and constraints. Context is delimited and explicitly treated as data. Example idea task:

```text
Generate {count} distinct content ideas.
Platform: {platform}
Content type: {content_type}
Audience: {audience}
Tone: {tone}
Topic supplied by the user: <topic>{topic}</topic>
Additional instructions: <instructions>{instructions}</instructions>
Return only data that matches the supplied response schema.
Do not invent factual claims, sources, or performance guarantees.
```

Do not concatenate user text into system instructions. Set output length bounds and store a `prompt_version` with each generation audit record.

## Generation transaction

1. Authenticate and load the project through an ownership-scoped query.
2. Validate workflow prerequisites and the idempotency key.
3. Create an audit row with `pending` status and commit it.
4. Call the provider outside a long-running database transaction.
5. Validate and normalize the response.
6. In one short transaction, insert generated entities and mark the audit row `succeeded`.
7. On failure, mark the audit row `failed` with a stable error code; do not persist partial content.

## Automation hooks

- Generate API client types from `/openapi.json` during CI.
- Run prompt contract tests with a fake provider on every commit.
- Run real provider evaluations manually or nightly with a strict spend limit.
- Maintain a small JSONL evaluation set covering each platform, ambiguous topics, long inputs, refusal behavior, and schema adherence.
- Track latency, failure rate, token usage, and estimated cost by provider/model/prompt version.

## Content safeguards

- Display generated content as a draft requiring user review.
- Sanitize rendered HTML; store Markdown or editor JSON rather than trusted raw HTML.
- Add abuse and rate controls before public access.
- Minimize prompt/audit retention and provide project deletion semantics.
- For factual content, ask the model to mark claims needing verification; automated fact checking remains outside the SRS MVP.
