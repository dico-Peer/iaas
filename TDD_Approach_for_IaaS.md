# IaaS TDD Approach — User Stories & Epics

**Version:** 1.0  
**Last Updated:** February 2026  
**Purpose:** Define a Test-Driven Development workflow for implementing IaaS user stories and epics  
**References:** IaaS_Complete_Concept.md, iaas_wireframes.html

---

## 1. Executive Summary

This document defines a **TDD-first approach** for implementing the IaaS platform, aligning the concept document's testing strategy with the wireframes and story-level backlog. The approach ensures:

- **Tests written before implementation** for every user story
- **≥90% coverage** for business logic, ≥80% overall
- **Acceptance criteria** drive test design (Given/When/Then)
- **Wireframes** inform E2E and component test scenarios
- **Epic → Story → Test** traceability

---

## 2. Scope Overview

### 2.1 MVP Epics (Implementation Order)

| Epic | Sprint | Weeks | Stories | Points | Key Deliverables |
|------|--------|-------|---------|--------|------------------|
| **EPIC 1:** Infrastructure & Auth | 1 | 1-2 | 5 | 31 | CI/CD, DB, Auth, Shell, Guards |
| **EPIC 2:** Interview Project & Question Designer | 2 | 3-4 | 6 | 60 | Projects CRUD, Questions, Branching, AI Gen, Templates |
| **EPIC 3:** Agent Configuration & Orchestration | 3 | 5-6 | 3 | 26 | Agents, Prompts, Archetypes, Test Interview |
| **EPIC 4:** Text Conversation Engine | 3-4 | 5-8 | 4 | 47 | Chat, WebSocket, Follow-ups, Pause/Resume |
| **EPIC 5:** Voice Interview Engine | 4-5 | 7-10 | 3 | 29 | WebRTC, STT, TTS, Transcript |
| **EPIC 6:** Analysis Engine | 5-6 | 9-12 | 4 | 42 | Themes, Sentiment, Quotes, Export |
| **EPIC 7:** Enterprise & Compliance | 6-7 | 11-14 | 5 | 60 | SSO, RBAC, Consent, Audit, Participant Mgmt |

### 2.2 Wireframe-to-Epic Mapping

| Wireframe Screen | Primary Epic | User Stories |
|-----------------|--------------|--------------|
| Login Page | EPIC 1 | US-1.03 (Auth) |
| Dashboard | EPIC 1, 2 | US-1.04 (Shell), US-2.01 (Projects) |
| Projects List | EPIC 2 | US-2.01 |
| New Project Wizard (6 steps) | EPIC 2 | US-2.01, US-2.02, US-3.01 |
| Project Detail (Overview, Questions, Agents, Testing, Monitoring, etc.) | EPIC 2, 3, 6, 7 | US-2.02–2.06, US-3.01–3.06 |
| Question Editor | EPIC 2 | US-2.02, US-2.03, US-2.04 |
| Agent List / Flow Designer / Weights | EPIC 3 | US-3.01–3.06 |
| Chat Simulation (Testing tab) | EPIC 3, 4 | US-3.06, US-4.x |
| Interviewee Flow (Landing → Consent → Chat → Pause → Complete) | EPIC 4, 5, 7 | US-4.x, US-5.x, US-7.x (Consent) |
| Team Management | EPIC 1, 7 | US-1.05, US-7.x |
| Templates Library | EPIC 2 | US-2.06 |
| Settings (Profile, Org, Auth, Data, Billing) | EPIC 1, 7 | US-1.x, US-7.x |

---

## 3. TDD Workflow

### 3.1 Core TDD Cycle (Per User Story)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. RED — Write failing test(s) from acceptance criteria                  │
│    • Unit: pytest (backend) / Vitest (frontend)                           │
│    • Integration: DB, Redis, API contracts                               │
│    • E2E: Playwright for critical user flows                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. GREEN — Implement minimum code to pass                                │
│    • No gold-plating; satisfy spec only                                  │
│    • Run: make test (parallel pytest + Jest)                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. REFACTOR — Improve clarity, remove duplication                         │
│    • Ensure tests still pass                                             │
│    • Run: make lint, make type-check                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. COMMIT — Atomic commit: test + implementation                         │
│    • CI runs on push; must pass before merge                             │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Test Pyramid by Layer

| Layer | Tool | Coverage Target | When to Write |
|-------|------|-----------------|---------------|
| **Unit** | pytest, Vitest | 90%+ business logic | First (RED phase) |
| **Integration** | pytest + test DB/Redis | API contracts, DB, events | With unit tests |
| **E2E** | Playwright | Critical paths (login, interview flow) | After unit/integration pass |
| **Performance** | k6 | p99 < 200ms API | Post-MVP |

### 3.3 Priority Coverage (from Concept Doc)

| Area | Target | Rationale |
|------|--------|-----------|
| Conversation engine | 98% | Core IP, must be bulletproof |
| Follow-up logic | 98% | Critical for quality |
| Auth & RBAC | 99% | Enterprise security |
| Voice pipeline | 90% | Complex, real-time |
| Database queries | 85% | Integrity |

---

## 4. Story-Level TDD Process

### 4.1 For Each User Story

1. **Extract acceptance criteria** from the concept doc (Given/When/Then format).
2. **Map to wireframes** — identify UI elements and flows to test.
3. **Create test specification table** (see template below).
4. **Write tests first** — one test file per story or logical grouping.
5. **Implement** — satisfy tests only.
6. **Refactor** — clean up without changing behavior.

### 4.2 Test Specification Template

For each user story, maintain a table like this (aligned with IaaS_Complete_Concept.md):

| Test File | Test Function | Asserts |
|-----------|--------------|---------|
| `tests/unit/<module>/test_<feature>.py` | `test_<scenario>_<expected>()` | Description of what is verified |

**Example (US-2.02 — Add Question):**

| Test File | Test Function | Asserts |
|-----------|--------------|---------|
| `tests/frontend/questions/test_question_editor.test.tsx` | `test_add_question_open_ended()` | New card with text input, type=open-ended |
| `tests/frontend/questions/test_question_editor.test.tsx` | `test_add_question_rating_shows_scale_fields()` | Type=rating → min/max fields appear |
| `tests/unit/questions/test_question_endpoints.py` | `test_create_question()` | POST /questions creates record |

### 4.3 Given/When/Then → Test Mapping

| Acceptance Criteria | Test Type | Example |
|---------------------|-----------|---------|
| **Given** X, **when** Y, **then** Z | Unit or Integration | `test_given_valid_credentials_when_login_then_200_with_tokens()` |
| UI behavior | Component / E2E | `test_sidebar_shows_all_items()` |
| API contract | Integration | `test_post_projects_returns_201_with_project()` |
| Performance | Performance | `test_dashboard_loads_under_2_seconds()` |

---

## 5. Epic-by-Epic TDD Checklist

### EPIC 1: Infrastructure & Auth (Sprint 1)

| Story | Focus | Test First | Key Tests |
|-------|-------|------------|-----------|
| US-1.01 | CI/CD, Repo structure | `tests/ci/test_workflows.py` | Lint, type-check, test stage < 5 min |
| US-1.02 | Migrations, DB schema | `tests/unit/migrations/`, `tests/integration/test_migrations.py` | All tables, FKs, pgvector |
| US-1.03 | Auth (register, login, JWT) | `tests/unit/auth/test_auth_endpoints.py` | 201 on register, 200 on login, 401 on invalid |
| US-1.04 | App shell, sidebar, routing | `tests/frontend/app/test_shell.test.tsx` | Sidebar items, role-based visibility |
| US-1.05 | User invite, RBAC | `tests/unit/users/test_user_endpoints.py` | Invite, accept, list, 403 for non-admin |

**Wireframe coverage:** Login, Dashboard, Sidebar, TopBar, Settings (Profile, Auth).

---

### EPIC 2: Interview Project & Question Designer (Sprint 2)

| Story | Focus | Test First | Key Tests |
|-------|-------|------------|-----------|
| US-2.01 | Projects CRUD | `tests/unit/projects/test_project_endpoints.py` | Create, list, update, delete, clone |
| US-2.02 | Question editor | `tests/frontend/questions/test_question_editor.test.tsx` | Add, reorder, save, validation |
| US-2.03 | Branching rules | `tests/unit/questions/test_branching.py` | Condition types, target, circular detection |
| US-2.04 | AI question generation | `tests/unit/questions/test_ai_generate.py` | POST generate, 8–12 questions, mock LLM |
| US-2.05 | Templates | `tests/unit/templates/test_templates.py` | List, preview, use, save as template |
| US-2.06 | Test interview | `tests/frontend/testing/test_interview_simulation.test.tsx` | Split-screen, persona, debug panel |

**Wireframe coverage:** New Project Wizard (all 6 steps), Project Detail (Questions tab), Templates Library.

---

### EPIC 3: Agent Configuration & Orchestration (Sprint 3)

| Story | Focus | Test First | Key Tests |
|-------|-------|------------|-----------|
| US-3.01 | Agent CRUD, prompts | `tests/unit/agents/test_agent_endpoints.py` | Create, version, variable insertion |
| US-3.02 | Archetypes | `tests/unit/agents/test_archetypes.py` | 6 archetypes, pre-filled prompts |
| US-3.03 | Test prompt / preview | `tests/frontend/agents/test_agent_preview.test.tsx` | 3-message exchange, reasoning |

**Wireframe coverage:** Agents tab (List, Flow Designer, Weights), New Project Wizard step 3 (Agents).

---

### EPIC 4: Text Conversation Engine (Sprint 3–4)

| Story | Focus | Test First | Key Tests |
|-------|-------|------------|-----------|
| US-4.01 | Create conversation, opening message | `tests/unit/conversations/test_conversation_endpoints.py` | POST conversation, first agent message |
| US-4.02 | Send message, follow-up | `tests/unit/conversations/test_message_flow.py` | POST message, agent response < 3s |
| US-4.03 | WebSocket live delivery | `tests/integration/conversations/test_websocket.py` | Message broadcast, typing indicator |
| US-4.04 | Pause/resume | `tests/unit/conversations/test_pause_resume.py` | Pause, resume, 7-day persistence |

**Wireframe coverage:** Interviewee Chat, Interviewee Paused, Project Detail Testing tab (chat simulation).

---

### EPIC 5: Voice Interview Engine (Sprint 4–5)

| Story | Focus | Test First | Key Tests |
|-------|-------|------------|-----------|
| US-5.01 | Voice session start | `tests/unit/voice/test_voice_endpoints.py` | POST start, WebRTC signaling |
| US-5.02 | STT transcription | `tests/integration/voice/test_stt.py` | Mock Deepgram, transcript stored |
| US-5.03 | TTS synthesis | `tests/integration/voice/test_tts.py` | Mock ElevenLabs, audio < 500ms |

**Wireframe coverage:** (Voice UI implied; extend Interviewee Chat for voice mode.)

---

### EPIC 6: Analysis Engine (Sprint 5–6)

| Story | Focus | Test First | Key Tests |
|-------|-------|------------|-----------|
| US-6.01 | Trigger analysis | `tests/unit/analysis/test_analysis_jobs.py` | POST trigger, job queued |
| US-6.02 | Themes, sentiment | `tests/unit/analysis/test_thematic_coder.py` | Themes extracted, sentiment score |
| US-6.03 | Export PDF/XLSX | `tests/unit/exports/test_export_service.py` | PDF generated, branded header |
| US-6.04 | Dashboard | `tests/frontend/analysis/test_analysis_dashboard.test.tsx` | Load < 2s, themes, heatmap |

**Wireframe coverage:** Project Detail Analysis tab, Costs tab.

---

### EPIC 7: Enterprise & Compliance (Sprint 6–7)

| Story | Focus | Test First | Key Tests |
|-------|-------|------------|-----------|
| US-7.01 | SSO (Auth0/Azure AD) | `tests/integration/auth/test_sso.py` | Redirect, callback, JWT |
| US-7.02 | Consent flow | `tests/frontend/interviewee/test_consent.test.tsx` | Checkboxes, continue disabled until all |
| US-7.03 | Audit log | `tests/unit/audit/test_audit_log.py` | All mutations logged |
| US-7.04 | Participant management | `tests/unit/participants/test_participants.py` | Invite, CSV import, tracking |
| US-7.05 | Data retention | `tests/integration/compliance/test_retention.py` | Auto-delete after N days |

**Wireframe coverage:** Interviewee Consent, Team Management, Settings (Data & Privacy, Authentication).

---

## 6. Wireframe-Driven E2E Scenarios

Based on `iaas_wireframes.html`, define these Playwright flows:

| Scenario | Steps | Epic |
|----------|-------|------|
| **Happy path: New project** | Login → Dashboard → New Project → Wizard steps 1–6 → Save as Draft | 1, 2, 3 |
| **Happy path: Interviewee** | Landing → Consent (all checked) → Chat (send 3 messages) → Pause → Resume → Complete | 4, 7 |
| **Designer: Question flow** | Project Detail → Questions tab → Add question → Drag reorder → Save | 2 |
| **Designer: Agent flow** | Project Detail → Agents tab → Add Agent → Flow Designer → Validate | 3 |
| **Analyst: View results** | Project Detail → Analysis tab → Filter → Export PDF | 6 |
| **Admin: Team** | Team → Invite member → Change role | 1, 7 |

---

## 7. Definition of Done (Per Story)

A user story is **done** when:

- [ ] All acceptance criteria have corresponding tests
- [ ] Tests written **before** implementation (TDD)
- [ ] Unit tests pass (`make test`)
- [ ] Integration tests pass (DB, Redis, API)
- [ ] E2E tests pass for affected flows (if applicable)
- [ ] Coverage: ≥90% for business logic, ≥80% overall
- [ ] Lint and type-check pass (`make lint`, `make type-check`)
- [ ] Wireframe behavior verified (manual or E2E)
- [ ] Audit logging in place for data mutations (where required)
- [ ] i18n keys added for new UI strings (DE + EN)
- [ ] WCAG 2.1 AA compliance for new UI components

---

## 8. Recommended Sprint Cadence

| Week | Sprint | Focus | TDD Emphasis |
|------|--------|-------|--------------|
| 1–2 | 1 | EPIC 1 | CI tests first, then auth, then shell |
| 3–4 | 2 | EPIC 2 | Project + question tests before UI |
| 5–6 | 3 | EPIC 3, start EPIC 4 | Agent tests, conversation API tests |
| 7–8 | 4 | EPIC 4, start EPIC 5 | WebSocket, voice session tests |
| 9–10 | 5 | EPIC 5, EPIC 6 | STT/TTS mocks, analysis job tests |
| 11–14 | 6–7 | EPIC 6, EPIC 7 | Export, SSO, consent, audit |

---

## 9. Tools & Commands

| Action | Command |
|--------|---------|
| Run all tests | `make test` |
| Backend only | `pytest tests/ -v` |
| Frontend only | `npm run test` (Vitest) |
| E2E | `npx playwright test` |
| Coverage | `pytest --cov=app tests/` |
| Lint | `make lint` (ruff + ESLint) |
| Type-check | `make type-check` (mypy + tsc) |
| Docker up | `docker-compose up` |
| Migrations | `alembic upgrade head` |

---

## 10. Next Steps

1. **Create test directory structure** matching the epic/story layout.
2. **Add test specification tables** to each story in the backlog (or a separate `TEST_SPECS.md`).
3. **Implement US-1.01** (CI/CD) first — establishes the TDD pipeline.
4. **Run first RED cycle** for US-1.02 (migrations) or US-1.03 (auth).
5. **Wire Playwright** to critical wireframe flows (login, interviewee flow).
6. **Track coverage** per epic in CI (e.g., Codecov) and fail builds below thresholds.

---

**Document Prepared:** February 2026  
**Status:** Ready for Development Kickoff
