# SRS Traceability Matrix

| Requirement | Design / implementation location | Verification |
|---|---|---|
| FR-AUTH-001 registration | auth routes/service, user repository, Argon2 | IT-001 valid, duplicate, invalid email/password |
| FR-AUTH-002 login/JWT | auth service and JWT core | IT-002 success, wrong password, expiry |
| FR-AUTH-003 bearer authorization | current-user dependency | ownership suite on all protected routes |
| FR-AUTH-005 profile | `/users/me` GET/PATCH | IT-004 read/update |
| FR-PROJ-001 create | project schema/service/repository | IT-005 create and validation |
| FR-PROJ-002/003 list/detail | ownership-scoped project queries | IT-006 pagination/detail/isolation |
| FR-PROJ-005 delete/cascade | FK cascades + delete service | IT-007 children removed |
| FR-IDEA-001/002 | idea service + AI provider schema | IT-008 count, context, persistence, failure |
| FR-OUT-001/002 | outline service + platform templates | IT-009 per-platform shape |
| FR-DRAFT-001/002 | draft service + structured result | E2E-001 full workflow |
| FR-EDIT-001/003 | editor + versioned PATCH | IT-010 save/reload/conflict |
| FR-AI-002 Factory Method | `app/ai/factory.py` | unit test provider selection |
| FR-REPO-001 Repository Pattern | `app/repositories` | service tests with fakes |
| NFR-PERF-001 | indexes, metrics, load test | p95 report for AI/non-AI |
| NFR-SEC-001 | Argon2 password helper | hash inspection and auth tests |
| NFR-SEC-003 | ownership-scoped repositories | cross-user matrix |
| NFR-SEC-004 | settings + secret manager | secret scan and deployment review |

## SRS decisions clarified in this blueprint

- The SRS lists alternatives; this scaffold selects React, FastAPI, and PostgreSQL.
- WebSockets appear in the table of contents but no WebSocket behavior is specified. The MVP uses HTTP and can add Server-Sent Events for streaming later.
- Project update, idea selection, list endpoints for generated artifacts, and conflict-safe draft saves are necessary supporting contracts even where the condensed SRS lists only headline endpoints.
- Automatic publishing, image/video generation, payments, collaboration, analytics, and automatic fact checking remain future enhancements.
