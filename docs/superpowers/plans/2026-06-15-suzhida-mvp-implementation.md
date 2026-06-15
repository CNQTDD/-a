# “诉智达”MVP Implementation Plan

> **For agentic workers:** REQUIRED: Use $subagent-driven-development (if subagents available) or $executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个可演示、可评估、可私有化部署的投诉智能处置 MVP，通过单 Agent + LangGraph 状态机完成投诉理解、Milvus/Elasticsearch 混合检索、有依据的方案生成、规则校验、人工确认与反馈闭环。

**Architecture:** 后端采用 FastAPI 作为 API/SSE 边界，LangGraph 负责单 Agent 状态流转和有限循环；检索层以 Milvus 为语义召回主库、Elasticsearch 为 BM25 补充，并通过 BGE reranker 重排。模型能力全部经过内部网关访问 vLLM、Embedding 和 Rerank 服务，前端采用 Vue 3 工作台展示阶段状态、证据、流式方案与人工反馈。

**Tech Stack:** Python 3.11、FastAPI、Pydantic v2、SQLAlchemy 2、Alembic、LangGraph、PyMilvus、Elasticsearch Python client、Redis、MySQL 8、httpx、structlog、pytest、Vue 3、TypeScript、Vite、Pinia、Vitest、Playwright、Docker Compose、vLLM、BGE-M3、BGE-reranker

**Reference Spec:** `docs/superpowers/specs/2026-06-15-suzhida-complaint-agent-design.md`

**Command convention:** All commands are PowerShell commands run from the repository root unless a task says otherwise. Use `Push-Location <dir>; try { <command> } finally { Pop-Location }` for subdirectories. Do not use Bash-only `VAR=value command` syntax.

**Historical compatibility contract:** The resume project ran from 2025-06 through 2026-04. Runtime dependencies, container images, APIs, and model capabilities must have public release dates on or before 2026-04-30. Superpowers is only the current reconstruction workflow and must not appear as an original project technology.

**Conservative version baseline:**

| Component | Pinned baseline | Timeline rationale |
|---|---:|---|
| Python | 3.11.x | Available before project start |
| FastAPI | 0.115.12 | Released 2025-03-23 |
| Pydantic | 2.11.5 | Released 2025-05-22 |
| SQLAlchemy | 2.0.41 | Released 2025-05-14 |
| LangGraph | 1.0.5 | Released 2025-12-12; documented late-project upgrade |
| vLLM | 0.8.5 | Released 2025-04-28 |
| PyMilvus / Milvus | 2.5.10 / 2.5.x | Available before project start |
| Elasticsearch client/server | 8.17.2 / 8.17.x | Available before project start |
| redis-py / Redis | 5.2.1 / 7.2.x | Available before project start |
| httpx | 0.28.1 | Released 2024-12-06 |
| Vue | 3.5.13 | Released 2024-11-15 |
| Pinia | 2.3.1 | Released 2025-01-20 |
| Vite / TypeScript | 6.1.x / 5.7.x | Available before project start |
| Vitest / Playwright | 3.0.x / 1.50.x | Available before project start |

Do not silently replace these with latest releases. Any upgrade must remain on or before the cutoff and be recorded in the acceptance report.

---

## File Structure

```text
.
├── AGENTS.md
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Makefile
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── errors.py
│   │   │   ├── dependencies.py
│   │   │   └── v1/
│   │   │       ├── router.py
│   │   │       ├── complaints.py
│   │   │       ├── feedback.py
│   │   │       ├── knowledge.py
│   │   │       └── metrics.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   ├── tracing.py
│   │   │   └── security.py
│   │   ├── domain/
│   │   │   ├── enums.py
│   │   │   ├── schemas.py
│   │   │   └── errors.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   ├── models/
│   │   │   │   ├── complaint.py
│   │   │   │   ├── knowledge.py
│   │   │   │   └── workflow.py
│   │   │   └── repositories/
│   │   │       ├── complaints.py
│   │   │       ├── feedback.py
│   │   │       └── knowledge.py
│   │   ├── gateways/
│   │   │   ├── llm.py
│   │   │   ├── embeddings.py
│   │   │   └── reranker.py
│   │   ├── retrieval/
│   │   │   ├── contracts.py
│   │   │   ├── milvus_store.py
│   │   │   ├── elastic_store.py
│   │   │   ├── template_store.py
│   │   │   └── hybrid.py
│   │   ├── knowledge/
│   │   │   ├── masking.py
│   │   │   ├── chunking.py
│   │   │   └── ingestion.py
│   │   ├── workflow/
│   │   │   ├── state.py
│   │   │   ├── prompts.py
│   │   │   ├── nodes/
│   │   │   │   ├── intent.py
│   │   │   │   ├── rewrite.py
│   │   │   │   ├── retrieve.py
│   │   │   │   ├── generate.py
│   │   │   │   ├── validate.py
│   │   │   │   └── feedback.py
│   │   │   ├── routing.py
│   │   │   ├── graph.py
│   │   │   └── service.py
│   │   ├── evaluation/
│   │   │   ├── dataset.py
│   │   │   ├── retrieval_metrics.py
│   │   │   └── runner.py
│   │   └── observability/
│   │       └── metrics.py
│   ├── scripts/
│   │   ├── ingest_knowledge.py
│   │   └── run_evaluation.py
│   └── tests/
│       ├── conftest.py
│       ├── unit/
│       ├── integration/
│       └── contract/
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   └── complaints.ts
│   │   ├── stores/
│   │   │   └── complaint.ts
│   │   ├── types/
│   │   │   └── complaint.ts
│   │   ├── views/
│   │   │   └── ComplaintWorkbench.vue
│   │   └── components/
│   │       ├── SessionSidebar.vue
│   │       ├── ComplaintComposer.vue
│   │       ├── WorkflowTimeline.vue
│   │       ├── SolutionPanel.vue
│   │       ├── EvidencePanel.vue
│   │       └── FeedbackBar.vue
│   └── tests/
│       ├── unit/
│       └── e2e/
├── data/
│   ├── samples/
│   └── evaluation/
└── docs/
    ├── superpowers/
    │   ├── specs/
    │   └── plans/
    ├── api/
    ├── deployment/
    └── evaluation/
```

---

## Chunk 1: Foundation And Persistence

### Task 1: Bootstrap Repository And Quality Gates

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `docker-compose.yml`
- Create: `Makefile`
- Create: `AGENTS.md`
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/unit/test_project_layout.py`
- Create: `frontend/package.json`
- Modify: `README.md`

- [ ] **Step 1: Verify or install the required runtimes**

Run:

```powershell
py -3.11 --version
node --version
npm --version
```

Expected: Python 3.11 and Node.js 20+ are available. If Python 3.11 is missing, run `winget install -e --id Python.Python.3.11 --scope user`, open a new PowerShell session, and rerun the version check. If Node.js 20+ is missing, run `winget install -e --id OpenJS.NodeJS.LTS --scope user`, reopen PowerShell, and rerun the checks.

- [ ] **Step 2: Create the minimum package manifests needed to run tests**

Create `backend/pyproject.toml` with the application metadata, dependencies, the `dev` extra, and pytest configuration. Create `frontend/package.json` with exact time-compatible versions: Vue `3.5.13`, Pinia `2.3.1`, Vite `6.1.x`, TypeScript `5.7.x`, Vitest `3.0.x`, Vue Test Utils `2.4.x`, and Playwright `1.50.x`. Add scripts named `dev`, `build`, `type-check`, `test`, and `test:e2e`. Generate and commit `package-lock.json`; do not use version ranges that can resolve to post-cutoff releases.

- [ ] **Step 3: Create and install the isolated backend development environment**

Run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e "backend[dev]"
```

Expected: installation succeeds and `.\.venv\Scripts\python.exe -m pytest --version` exits `0`.

- [ ] **Step 4: Write the repository smoke test**

Create `backend/tests/unit/test_project_layout.py`:

```python
from pathlib import Path


def test_required_project_files_exist() -> None:
    root = Path(__file__).parents[3]
    required = [
        root / ".env.example",
        root / "Makefile",
        root / "backend" / "pyproject.toml",
        root / "frontend" / "package.json",
    ]
    assert all(path.exists() for path in required)
```

- [ ] **Step 5: Run the smoke test and verify failure**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/test_project_layout.py -v } finally { Pop-Location }`

Expected: FAIL because `.env.example` and `Makefile` do not yet exist.

- [ ] **Step 6: Complete backend dependency and tool configuration**

In `backend/pyproject.toml`, declare the application dependencies and configure `pytest`, `ruff`, and `mypy`. Keep production adapters behind interfaces so unit tests can run without Milvus, Elasticsearch, Redis, MySQL, or a model server.

Required dependency groups:

```toml
[project]
requires-python = ">=3.11,<3.13"
dependencies = [
  "fastapi==0.115.12",
  "uvicorn[standard]==0.34.2",
  "pydantic==2.11.5",
  "pydantic-settings==2.9.1",
  "sqlalchemy==2.0.41",
  "alembic==1.15.2",
  "pymysql==1.1.1",
  "langgraph==1.0.5",
  "httpx==0.28.1",
  "pymilvus==2.5.10",
  "elasticsearch==8.17.2",
  "redis==5.2.1",
  "structlog==25.3.0",
  "prometheus-client==0.21.1",
]

[project.optional-dependencies]
dev = [
  "pytest==8.3.5",
  "pytest-asyncio==0.26.0",
  "pytest-cov==6.1.1",
  "mypy==1.15.0",
  "ruff==0.11.8",
  "respx==0.22.0",
]
```

- [ ] **Step 7: Add root development commands and documentation**

Create `.gitignore`, `.env.example`, `AGENTS.md`, `backend/app/__init__.py`, and `Makefile`. The `Makefile` must expose `backend-test`, `backend-lint`, `frontend-test`, `test`, `up`, and `down`. Add a skeleton `docker-compose.yml` with only a valid Compose name and empty service map; Task 19 replaces it with the runnable stack. The README must state that production inference is private vLLM and local tests use deterministic fakes.

- [ ] **Step 8: Add bootstrap test fixtures**

Implement `backend/tests/conftest.py` with:

- a temporary SQLite database with foreign-key enforcement for repository tests;
- transaction rollback between tests;
- a temporary directory fixture.

Tasks 2, 6, and 7 extend this file only after `Settings`, `create_app()`, and adapter contracts exist.

- [ ] **Step 9: Run the smoke test**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/test_project_layout.py -v } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 10: Run static configuration checks**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest -q } finally { Pop-Location }`

Expected: all current tests PASS.

- [ ] **Step 11: Commit**

```bash
git add .gitignore .env.example docker-compose.yml Makefile AGENTS.md README.md backend frontend/package.json
git commit -m "chore: bootstrap suzhida workspace"
```

### Task 2: Configuration, Logging, And Health API

**Files:**
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/logging.py`
- Create: `backend/app/core/tracing.py`
- Create: `backend/app/api/errors.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/unit/core/test_config.py`
- Create: `backend/tests/unit/core/test_logging.py`
- Create: `backend/tests/integration/api/test_health.py`
- Create: `backend/tests/integration/api/test_tracing.py`

- [ ] **Step 1: Write failing configuration tests**

```python
from app.core.config import Settings


def test_settings_never_expose_raw_complaint_logging() -> None:
    assert not hasattr(Settings(), "log_raw_complaints")


def test_settings_use_versioned_api_prefix() -> None:
    assert Settings().api_prefix == "/api/v1"
```

- [ ] **Step 2: Run tests and verify import failure**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/core/test_config.py -v } finally { Pop-Location }`

Expected: FAIL because `app.core.config` does not exist.

- [ ] **Step 3: Implement typed settings**

Use `pydantic-settings`. Include environment, service name, API prefix, database URL, Redis URL, Milvus URI, Elasticsearch URL, LLM base URL, embedding URL, reranker URL, timeouts, and retry limit.

Do not expose a setting that can enable raw complaint logging. Add a production validator requiring non-empty private LLM, embedding, and reranker URLs and rejecting fake gateway schemes when `environment="production"`.

- [ ] **Step 4: Write the failing health endpoint test**

```python
def test_health_returns_service_status(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"service": "suzhida-api", "status": "ok"}
```

- [ ] **Step 5: Extend test fixtures and verify health test failure**

Extend `backend/tests/conftest.py` with a `Settings` override and a lazy FastAPI `TestClient` fixture that imports `create_app` only when the fixture is requested.

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/integration/api/test_health.py -v } finally { Pop-Location }`

Expected: FAIL because `backend/app/main.py` and `create_app()` do not exist.

- [ ] **Step 6: Implement the FastAPI app factory**

Expose `create_app()` and add request ID middleware. API errors must return:

```json
{"code": "ERROR_CODE", "message": "human readable message", "trace_id": "uuid"}
```

- [ ] **Step 7: Add logging and tracing safety tests**

Write tests proving:

- an inbound `X-Request-ID` is propagated or a UUID is generated;
- the error envelope contains the same trace ID;
- structured logs contain masked complaint text only;
- raw phone, identity number, email, and address values never appear in captured logs.

- [ ] **Step 8: Run logging/tracing tests and verify failure**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/core/test_logging.py tests/integration/api/test_tracing.py -v } finally { Pop-Location }`

Expected: FAIL because trace middleware and safe log processors are not implemented.

- [ ] **Step 9: Implement logging and tracing**

Implement request-scoped trace IDs and structlog processors that accept only already-masked domain fields. Never pass raw complaint text to the logger.

- [ ] **Step 10: Run focused tests**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/core tests/integration/api/test_health.py tests/integration/api/test_tracing.py -v } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 11: Commit**

```bash
git add backend/app/core backend/app/api/errors.py backend/app/main.py backend/tests
git commit -m "feat: add service configuration and health API"
```

### Task 3: Domain Schemas And Persistence

**Files:**
- Create: `backend/app/domain/enums.py`
- Create: `backend/app/domain/schemas.py`
- Create: `backend/app/domain/errors.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/db/models/complaint.py`
- Create: `backend/app/db/models/knowledge.py`
- Create: `backend/app/db/models/workflow.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/0001_initial_schema.py`
- Create: `backend/tests/unit/domain/test_schemas.py`
- Create: `backend/tests/integration/db/test_models.py`

- [ ] **Step 1: Write failing domain invariant tests**

```python
import pytest
from pydantic import ValidationError
from app.domain.schemas import FeedbackCreate


def test_rejected_feedback_requires_reason() -> None:
    with pytest.raises(ValidationError):
        FeedbackCreate(action="rejected")


def test_edited_feedback_requires_solution() -> None:
    with pytest.raises(ValidationError):
        FeedbackCreate(action="edited")
```

- [ ] **Step 2: Run the tests and verify failure**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/domain/test_schemas.py -v } finally { Pop-Location }`

Expected: FAIL because domain schemas do not exist.

- [ ] **Step 3: Implement enums and Pydantic schemas**

Define session status, feedback action, source type, validation status, and risk level. Add schemas for session creation, intent result, evidence, generated solution, validation result, SSE event, and feedback.

- [ ] **Step 4: Write failing persistence tests and run them**

Verify a session can own evidence, generated solutions, and one or more feedback records; deleting a session in a test transaction must clean dependent rows.

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/integration/db/test_models.py -v } finally { Pop-Location }`

Expected: FAIL because the SQLAlchemy models and migration do not exist.

- [ ] **Step 5: Implement SQLAlchemy models and initial migration**

Implement:

- `User`: UUID `id` PK, `name` varchar(100) not null, `role` enum not null, `status` enum not null.
- `ComplaintSession`: UUID `id` PK, `user_id` FK not null, unique nullable `client_request_id`, status/risk enums, masked text, JSON intent/emotion/entities, confidence decimal, workflow version, timestamps; index `(status, created_at)`.
- `RetrievedEvidence`: UUID `id` PK, `session_id` FK cascade, unique string `evidence_id`, string `source_id`, string `chunk_id`, source type, title/content snapshot, scores, JSON metadata; index `(session_id, rerank_score)`.
- `GeneratedSolution`: UUID `id` PK, `session_id` FK cascade, model/prompt versions, text, JSON cited evidence IDs, validation status/details, timestamp.
- `HumanFeedback`: UUID `id` PK, `session_id` FK cascade, idempotency key, payload fingerprint, action, edited solution/reason/note, timestamp; unique `(session_id, idempotency_key)`.
- `KnowledgeDocument`: UUID `id` PK, string `source_id`, source type/version/business type/status/import batch, effective/expiry timestamps; unique `(source_type, source_id, source_version)` and index `(status, business_type)`.

Store flexible entities and validation details as JSON. Store only masked complaint text. Citation ownership is enforced in application validation by resolving each cited evidence ID within the same session, not by a nonexistent join model.

- [ ] **Step 6: Run migration and model tests**

Run:

```powershell
$env:DATABASE_URL = "sqlite+pysqlite:///./.tmp/migration-test.db"
Push-Location backend
try {
  New-Item -ItemType Directory -Force .tmp | Out-Null
  ..\.venv\Scripts\python.exe -m alembic upgrade head
  ..\.venv\Scripts\python.exe -m pytest tests/unit/domain tests/integration/db -v
} finally {
  Pop-Location
  Remove-Item Env:DATABASE_URL
}
```

Expected: migration succeeds and tests PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/domain backend/app/db backend/alembic.ini backend/alembic backend/tests
git commit -m "feat: add complaint domain and persistence schema"
```

### Task 4: Session Repository And Idempotent Session API

**Files:**
- Create: `backend/app/db/repositories/complaints.py`
- Create: `backend/app/api/dependencies.py`
- Create: `backend/app/api/v1/router.py`
- Create: `backend/app/api/v1/complaints.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/unit/db/test_complaint_repository.py`
- Create: `backend/tests/integration/api/test_sessions.py`
- Create: `backend/tests/integration/api/test_get_session.py`
- Create: `backend/tests/integration/api/test_list_sessions.py`

- [ ] **Step 1: Write failing idempotency tests**

```python
def test_create_session_is_idempotent(client) -> None:
    headers = {"Idempotency-Key": "client-request-001"}
    payload = {"user_id": "11111111-1111-4111-8111-111111111111"}
    first = client.post("/api/v1/complaints/sessions", headers=headers, json=payload)
    second = client.post("/api/v1/complaints/sessions", headers=headers, json=payload)
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
```

- [ ] **Step 2: Run the API test and verify 404**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/integration/api/test_sessions.py -v } finally { Pop-Location }`

Expected: FAIL with 404.

- [ ] **Step 3: Implement repository and endpoint**

The repository owns transaction boundaries for session creation and lookup. Use the `ComplaintSession.client_request_id` unique constraint created in Task 3. The test fixture inserts UUID user `11111111-1111-4111-8111-111111111111` before creating sessions. Return `201` for a new session and `200` for an existing match.

- [ ] **Step 4: Write and run a failing atomic run-claim repository test**

Test two concurrent repository calls attempting to transition the same session from `created` to `running`; exactly one succeeds.

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/db/test_complaint_repository.py::test_claim_run_is_atomic -v } finally { Pop-Location }`

Expected: FAIL because atomic claiming is not implemented.

- [ ] **Step 5: Implement atomic run claiming**

Use a conditional update or row lock in the repository. API mapping to HTTP 409 is added with the message endpoint in Task 14.

- [ ] **Step 6: Write failing GET session test**

Assert `GET /api/v1/complaints/{session_id}` returns session status, recognition output, evidence, latest solution, validation details, and feedback; unknown sessions return 404.

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/integration/api/test_get_session.py -v } finally { Pop-Location }`

Expected: FAIL because the endpoint does not exist.

- [ ] **Step 7: Implement GET session endpoint**

Return the aggregate through repository projections without exposing raw complaint text.

- [ ] **Step 8: Write and run failing session history listing tests**

Add `GET /api/v1/complaints/sessions?user_id=...&limit=...&cursor=...`. Test user scoping, reverse chronological order, cursor pagination, and absence of raw complaint text.

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/integration/api/test_list_sessions.py -v } finally { Pop-Location }`

Expected: FAIL because the listing endpoint does not exist.

- [ ] **Step 9: Implement session history listing**

Add cursor-based repository projection and API response without raw complaint text.

- [ ] **Step 10: Run all backend tests**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest -q } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 11: Commit**

```bash
git add backend/app/db/repositories backend/app/api backend/app/main.py backend/tests
git commit -m "feat: add idempotent complaint sessions"
```

---

## Chunk 2: Knowledge And Retrieval

### Task 5: Sensitive Data Masking And Knowledge Chunking

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/app/knowledge/masking.py`
- Create: `backend/app/knowledge/chunking.py`
- Create: `backend/tests/unit/knowledge/test_masking.py`
- Create: `backend/tests/unit/knowledge/test_chunking.py`
- Create: `data/samples/complaints.jsonl`
- Create: `data/samples/rules.md`

- [ ] **Step 1: Write failing masking tests**

```python
from app.knowledge.masking import mask_sensitive_text


def test_masks_phone_and_identity_number() -> None:
    text = "客户电话13812345678，身份证530102199001011234"
    result = mask_sensitive_text(text)
    assert "13812345678" not in result.text
    assert "530102199001011234" not in result.text
    assert "138****5678" in result.text
    assert result.categories == {"phone", "identity_number"}
```

- [ ] **Step 2: Run tests and verify failure**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/knowledge/test_masking.py -v } finally { Pop-Location }`

Expected: FAIL because masking does not exist.

- [ ] **Step 3: Implement deterministic masking**

Mask phone numbers, identity numbers, email addresses, and configurable address patterns before logging or knowledge ingestion. Return both masked text and detected entity categories; never retain original values in logs. Add false-positive cases for order numbers and ordinary long numeric IDs, plus captured-log assertions for every sensitive category.

- [ ] **Step 4: Write failing chunking tests**

Test that rule headings and article numbers are preserved in chunk metadata, defaults stay within 300–600 tokens with 50–80 token overlap, overlap does not duplicate an entire chunk, and metadata includes region, product, source time, effective time, expiry time, and article number when available.

- [ ] **Step 5: Implement structure-aware chunking**

Historical complaints produce one normalized record with complaint, cause, process, and result fields. Rules split by headings/articles with `source_id`, `source_version`, `article_number`, `business_type`, and `effective_at`.

- [ ] **Step 6: Run knowledge unit tests**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/knowledge -v } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/core/security.py backend/app/knowledge backend/tests/unit/knowledge data/samples
git commit -m "feat: add safe knowledge preprocessing"
```

### Task 6: Model Gateway Contracts And Deterministic Fakes

**Files:**
- Create: `backend/app/gateways/llm.py`
- Create: `backend/app/gateways/embeddings.py`
- Create: `backend/app/gateways/reranker.py`
- Create: `backend/tests/unit/gateways/test_llm_gateway.py`
- Create: `backend/tests/unit/gateways/test_embedding_gateway.py`
- Create: `backend/tests/unit/gateways/test_reranker_gateway.py`

- [ ] **Step 1: Write failing gateway contract tests**

```python
async def test_llm_gateway_retries_one_timeout(fake_transport) -> None:
    gateway = build_gateway(fake_transport, max_retries=1)
    result = await gateway.complete_json(messages=[{"role": "user", "content": "test"}])
    assert result == {"intent": "billing"}
    assert fake_transport.calls == 2
```

- [ ] **Step 2: Run tests and verify failure**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/gateways -v } finally { Pop-Location }`

Expected: FAIL because gateways do not exist.

- [ ] **Step 3: Implement OpenAI-compatible LLM gateway**

Use `httpx.AsyncClient`. Support structured JSON completion and streaming completion. Retry only timeout and retryable 5xx errors once; do not retry validation errors or 4xx responses. Emit a sanitized audit record with request ID, endpoint kind, model/version, latency, status, and token usage. Tests must prove raw sensitive values are absent.

- [ ] **Step 4: Implement embedding and reranker gateways**

Expose small typed methods:

```python
async def embed_texts(texts: list[str]) -> list[list[float]]: ...
async def rerank(query: str, documents: list[str]) -> list[float]: ...
```

Tests use deterministic fakes and never require GPU/model services.

Add timeout, malformed-response, 4xx, retryable 5xx, and exhausted-retry tests for both embedding and reranker gateways. A reranker outage must be distinguishable from an empty score list.

Embedding and reranker calls emit the same sanitized audit envelope as LLM calls: request ID, gateway kind, model/version, latency, status, and available usage/count fields. Add leakage tests for all three gateways.

- [ ] **Step 5: Run tests**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/gateways -v } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/gateways backend/tests/unit/gateways
git commit -m "feat: add private model gateway contracts"
```

### Task 7: Milvus Vector Store

**Files:**
- Create: `backend/app/retrieval/contracts.py`
- Create: `backend/app/retrieval/milvus_store.py`
- Create: `backend/tests/unit/retrieval/test_milvus_store.py`
- Create: `backend/tests/contract/test_milvus_contract.py`

- [ ] **Step 1: Write failing vector-store contract tests**

Test collection initialization, upsert idempotency, metadata filtering by exact registry-selected version/business type/effective time, expiry exclusion, and ordered top-k results.

```python
results = await store.search(
    vector=[0.1, 0.2],
    limit=5,
    filters={"source_version": "2026-06-demo", "business_type": "billing"},
)
assert [item.source_id for item in results] == ["rule-2", "case-7"]
```

- [ ] **Step 2: Run unit contract tests**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/retrieval/test_milvus_store.py -v } finally { Pop-Location }`

Expected: FAIL because the adapter does not exist.

- [ ] **Step 3: Implement the Milvus adapter**

Use a stable `chunk_id`/`evidence_id` as the primary key because one source can create multiple chunks. Store source ID, dense vector, source type, business type, region, product, version, status, source timestamp, effective/expiry timestamps, article number, and content snapshot. Keep Milvus-specific expressions inside this adapter.

- [ ] **Step 4: Add container-backed contract test marker**

Contract tests must skip unless `RUN_INFRA_TESTS=1`; when enabled, they create an isolated test collection and remove it after the test.

- [ ] **Step 5: Run unit tests**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/retrieval/test_milvus_store.py -v } finally { Pop-Location }`

Expected: PASS with a fake Milvus client.

- [ ] **Step 6: Run the optional Milvus contract**

Run:

```powershell
$env:RUN_INFRA_TESTS = "1"
Push-Location backend
try { ..\.venv\Scripts\python.exe -m pytest tests/contract/test_milvus_contract.py -v }
finally { Pop-Location; Remove-Item Env:RUN_INFRA_TESTS }
```

Expected: PASS when Milvus is running; otherwise this step is deferred to Task 19 and recorded as not run.

- [ ] **Step 7: Commit**

```bash
git add backend/app/retrieval/contracts.py backend/app/retrieval/milvus_store.py backend/tests
git commit -m "feat: add milvus vector retrieval adapter"
```

### Task 8: Elasticsearch And Redis Template Stores

**Files:**
- Create: `backend/app/retrieval/elastic_store.py`
- Create: `backend/app/retrieval/template_store.py`
- Create: `backend/tests/unit/retrieval/test_elastic_store.py`
- Create: `backend/tests/unit/retrieval/test_template_store.py`
- Create: `backend/tests/contract/test_elasticsearch_contract.py`
- Create: `backend/tests/contract/test_redis_contract.py`

- [ ] **Step 1: Write failing BM25 tests**

Verify exact rule numbers, product names, and tariff terms rank above semantically related but lexically different content.

- [ ] **Step 2: Implement Elasticsearch adapter**

Store full text and filterable metadata, including `chunk_id`, region, product, source/effective/expiry times, and article number. Build a bool query combining multi-match fields with the exact registry-selected source version, business type, effective time, and expiry filters.

- [ ] **Step 3: Write failing template lookup tests**

Test that a template is returned only when intent, business type, and minimum confidence all match; expired templates are ignored.

- [ ] **Step 4: Implement Redis template store**

Use versioned keys and JSON payloads. A template participates only when intent, business type, confidence threshold, status, and effective period match. Treat Redis errors as cache misses, return `degraded_sources=["redis"]`, and emit a degradation metric.

- [ ] **Step 5: Implement and run infrastructure contracts**

Implement isolated Elasticsearch index and Redis key-prefix contract tests with cleanup. Run:

```powershell
$env:RUN_INFRA_TESTS = "1"
Push-Location backend
try {
  ..\.venv\Scripts\python.exe -m pytest tests/contract/test_elasticsearch_contract.py tests/contract/test_redis_contract.py -v
} finally {
  Pop-Location
  Remove-Item Env:RUN_INFRA_TESTS
}
```

Expected: PASS when services are running; otherwise defer to Task 19 and record the reason.

- [ ] **Step 6: Run focused tests**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/retrieval/test_elastic_store.py tests/unit/retrieval/test_template_store.py -v } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/retrieval backend/tests
git commit -m "feat: add keyword and template retrieval"
```

### Task 9: Hybrid Retrieval, Fusion, And Reranking

**Files:**
- Create: `backend/app/retrieval/hybrid.py`
- Create: `backend/tests/unit/retrieval/test_hybrid.py`
- Create: `backend/tests/integration/retrieval/test_degradation.py`

- [ ] **Step 1: Write failing reciprocal-rank fusion tests**

```python
def test_fusion_deduplicates_and_preserves_sources() -> None:
    fused = fuse(vector_hits, keyword_hits)
    assert len({item.source_id for item in fused}) == len(fused)
    assert fused[0].source_id == "rule-101"
```

- [ ] **Step 2: Write failing degradation tests**

Cover:

- Milvus unavailable -> Elasticsearch-only with `degraded_sources=["milvus"]`.
- Elasticsearch unavailable -> Milvus-only with `degraded_sources=["elasticsearch"]`.
- Both unavailable -> `RetrievalUnavailable`, no generation.
- Reranker unavailable -> fused ordering remains, with `degraded_sources=["reranker"]`.
- Configured minimum score boundary -> below-threshold evidence is excluded.
- Duplicate chunks from both stores -> deduplicate by `chunk_id`, not by source document.
- Ties, empty results, and adapter timeouts remain deterministic.

- [ ] **Step 3: Implement hybrid retrieval**

Run Milvus and Elasticsearch concurrently, normalize results with configurable weighted reciprocal-rank fusion, deduplicate by `chunk_id`, apply configurable score thresholds, call BGE reranker, and return Top-5 plus Top-3 generation evidence. Configuration values are versioned inputs for offline tuning.

- [ ] **Step 4: Run retrieval tests**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/retrieval tests/integration/retrieval -v } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/retrieval/hybrid.py backend/tests
git commit -m "feat: add resilient hybrid retrieval"
```

### Task 10: Knowledge Ingestion Service And CLI

**Files:**
- Create: `backend/app/knowledge/ingestion.py`
- Create: `backend/app/db/repositories/knowledge.py`
- Create: `backend/scripts/ingest_knowledge.py`
- Create: `backend/tests/unit/knowledge/test_ingestion.py`
- Create: `backend/tests/integration/knowledge/test_ingestion_pipeline.py`
- Create: `docs/api/knowledge-ingestion.md`

- [ ] **Step 1: Write failing ingestion tests**

Test batch status transitions `pending -> processing -> staged -> active`, partial failures are recorded, rerunning the same source/version is idempotent, and inactive versions are excluded from default retrieval. Add failure injection after MySQL staging, Milvus write, Elasticsearch write, and activation.

- [ ] **Step 2: Implement ingestion orchestration**

Pipeline: parse -> mask -> chunk -> embed -> persist staged batch -> write version-tagged Milvus records -> write version-tagged Elasticsearch records -> verify counts -> atomically switch the active-version registry in MySQL from the previous version to the new version. Retrieval reads the active version from that registry and filters both stores by the exact version, so the single MySQL transaction is the visibility switch; external records do not maintain independent active flags. On failure, preserve the previous registry value, mark the batch failed, and run idempotent compensating cleanup for the unreferenced version-tagged records. Old versions remain query-invisible and may be cleaned asynchronously after the audit retention period.

- [ ] **Step 3: Implement CLI**

Command:

```powershell
Push-Location backend
try { ..\.venv\Scripts\python.exe scripts/ingest_knowledge.py --source ../data/samples --version 2026-06-demo }
finally { Pop-Location }
```

Expected output includes total documents, chunks, masked fields, failures, and activated version.

- [ ] **Step 4: Run tests**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/knowledge tests/integration/knowledge -v } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/knowledge backend/app/db/repositories/knowledge.py backend/scripts backend/tests docs/api
git commit -m "feat: add versioned knowledge ingestion"
```

---

## Chunk 3: Agent Workflow And API

### Task 11: Workflow State, Prompts, Intent, And Query Rewrite

**Files:**
- Create: `backend/app/workflow/state.py`
- Create: `backend/app/workflow/prompts.py`
- Create: `backend/app/workflow/nodes/intent.py`
- Create: `backend/app/workflow/nodes/rewrite.py`
- Create: `backend/tests/unit/workflow/test_intent_node.py`
- Create: `backend/tests/unit/workflow/test_rewrite_node.py`

- [ ] **Step 1: Write failing structured-output tests**

Test valid intent parsing, malformed JSON rejection, unknown intent fallback, and preservation of the original customer claim during rewrite.

- [ ] **Step 2: Implement typed workflow state**

Use `TypedDict` or Pydantic-compatible runtime state with explicit reducer behavior for events and evidence. Split it into:

- transient input containing raw complaint text, never passed to the checkpointer;
- checkpoint-safe state containing only masked complaint text, derived entities, evidence IDs, workflow counters, and generated output.

Add a serialization test proving phone, identity number, email, and address values are absent from the checkpoint payload.

- [ ] **Step 3: Implement intent and rewrite nodes**

Prompts must request strict JSON. The intent result contains intent, emotion, request, entities, confidence, and risk signals. The rewrite result contains normalized query and search filters.

- [ ] **Step 4: Run tests**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/workflow/test_intent_node.py tests/unit/workflow/test_rewrite_node.py -v } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/workflow backend/tests/unit/workflow
git commit -m "feat: add complaint understanding nodes"
```

### Task 12: Retrieval, Generation, And Validation Nodes

**Files:**
- Create: `backend/app/workflow/nodes/retrieve.py`
- Create: `backend/app/workflow/nodes/generate.py`
- Create: `backend/app/workflow/nodes/validate.py`
- Create: `backend/app/db/repositories/evidence.py`
- Create: `backend/tests/unit/workflow/test_retrieve_node.py`
- Create: `backend/tests/unit/workflow/test_generate_node.py`
- Create: `backend/tests/unit/workflow/test_validate_node.py`
- Create: `backend/tests/integration/workflow/test_citation_ownership.py`

- [ ] **Step 1: Write failing retrieval-node tests**

Test that Redis templates can short-circuit low-complexity scenarios while still attaching rule evidence, and that total retrieval failure marks the session for human review.

- [ ] **Step 2: Implement retrieval node**

Return `retrieved_evidence`, `generation_evidence`, `degraded_sources`, and retrieval confidence.

- [ ] **Step 3: Write failing generation tests**

Verify the generated schema contains assessment, steps, risk notice, and evidence IDs. Reject citations not present in `generation_evidence`.

- [ ] **Step 4: Implement generation node**

Stream content through the workflow event sink while building a final typed solution. The prompt must explicitly prohibit unauthorized refund/compensation/time commitments.

- [ ] **Step 5: Write failing validation tests**

Cover missing citations, invalid evidence IDs, sensitive promises, incomplete structure, low retrieval confidence, and high-risk complaints.

- [ ] **Step 6: Implement deterministic validator**

Return `passed`, `reason_codes`, `risk_level`, and `recommended_route`. Do not use an LLM for rules that can be deterministic.

- [ ] **Step 7: Write and run the failing citation ownership test**

Persist evidence for two sessions and assert a generated solution may cite only evidence owned by its own session.

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/integration/workflow/test_citation_ownership.py -v } finally { Pop-Location }`

Expected: FAIL because same-session citation resolution is not implemented.

- [ ] **Step 8: Implement same-session citation resolution**

Implement `backend/app/db/repositories/evidence.py` and resolve cited IDs through it, always scoped by `session_id`; fail validation when any ID is missing or belongs to another session.

- [ ] **Step 9: Run tests**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/workflow tests/integration/workflow/test_citation_ownership.py -v } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add backend/app/workflow/nodes backend/app/db/repositories/evidence.py backend/tests/unit/workflow backend/tests/integration/workflow/test_citation_ownership.py
git commit -m "feat: add evidence-grounded solution nodes"
```

### Task 13: LangGraph Routing, Finite Loops, And Human Interrupt

**Files:**
- Create: `backend/app/workflow/routing.py`
- Create: `backend/app/workflow/graph.py`
- Create: `backend/app/workflow/service.py`
- Modify: `backend/app/db/models/workflow.py`
- Create: `backend/alembic/versions/0002_workflow_runtime.py`
- Create: `backend/tests/unit/workflow/test_routing.py`
- Create: `backend/tests/integration/workflow/test_graph.py`
- Create: `backend/tests/integration/workflow/test_resume.py`
- Create: `backend/tests/integration/workflow/test_checkpoint_privacy.py`

- [ ] **Step 1: Write failing routing table tests**

```python
def test_missing_evidence_retries_retrieval_until_limit() -> None:
    state = state_with(reason_codes=["MISSING_EVIDENCE"], retry_count=0)
    assert route_after_validation(state) == "rewrite"


def test_retry_limit_routes_to_human() -> None:
    state = state_with(reason_codes=["MISSING_EVIDENCE"], retry_count=2)
    assert route_after_validation(state) == "human_review"
```

- [ ] **Step 2: Implement pure routing functions**

Keep branch logic independent of LangGraph so it can be exhaustively unit tested. Define precedence for conflicting reason codes and a single global `automatic_retry_count`. Increment it in a dedicated transition before either rewrite or generation retry; both retry types share the same maximum of two.

- [ ] **Step 3: Write failing graph integration tests**

Cover happy path, retrieval retry, generation-only retry, mixed retries, high-risk direct human route, two-source outage, and retry exhaustion. Assert exact node execution counts and no path executes more than two automatic retries. Validation success must still interrupt for mandatory human confirmation.

- [ ] **Step 4: Build and compile the LangGraph**

Graph order:

```text
intent -> rewrite -> retrieve -> generate -> validate
validate -> rewrite | generate | human_review
human_review -> feedback -> END
```

Create workflow checkpoint/run models and the `0002` migration. Use a database-backed checkpointer suitable for resuming after human review. The production path must never serialize transient raw input.

- [ ] **Step 5: Implement interrupt/resume service**

The service starts a run, persists checkpoint identity, returns `human_review_required`, and resumes only after a valid human action. Add a test that destroys and recreates the workflow service before resuming to prove process-restart recovery.

- [ ] **Step 6: Run workflow tests**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/workflow tests/integration/workflow -v } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/workflow backend/app/db/models/workflow.py backend/alembic/versions/0002_workflow_runtime.py backend/tests
git commit -m "feat: orchestrate finite complaint workflow"
```

### Task 14: SSE Message Endpoint And Durable Events

**Files:**
- Modify: `backend/app/api/v1/complaints.py`
- Modify: `backend/app/db/models/workflow.py`
- Create: `backend/alembic/versions/0003_workflow_events.py`
- Create: `backend/app/db/repositories/workflow_events.py`
- Create: `backend/app/api/v1/sse.py`
- Create: `backend/tests/integration/api/test_message_stream.py`
- Create: `backend/tests/integration/api/test_sse_reconnect.py`
- Create: `docs/api/sse-events.md`

- [ ] **Step 1: Write failing SSE contract tests**

Assert events are emitted in the documented order and each event contains `event_id`, `session_id`, `trace_id`, `type`, and `data`. Add duplicate, out-of-order, unknown `Last-Event-ID`, and active-run replay/live handoff cases.

- [ ] **Step 2: Implement durable event storage**

Create the workflow event model, sequence uniqueness constraint, and migration. Persist every externally visible event before sending it. Aggregate model output into bounded generation-delta events, for example every 100–250 ms or 256 characters, and persist each aggregate with a stable event ID. `Last-Event-ID` therefore always references a replayable event; persist the final solution separately.

- [ ] **Step 3: Implement SSE endpoint**

Use two endpoints to avoid POST/EventSource and reconnect ambiguity:

```text
POST /api/v1/complaints/{session_id}/messages
  -> atomically claims the session, starts a background workflow, returns 202 with run_id

GET /api/v1/complaints/{session_id}/events
  -> SSE replay/live stream; accepts Last-Event-ID
```

The producer runs independently of the HTTP streaming request. The GET endpoint replays persisted events, then atomically hands off to live events with event-ID deduplication. Reconnect never starts another workflow and never conflicts with the running-session guard.

- [ ] **Step 4: Test client disconnect behavior**

Disconnect the test client after retrieval, allow the independent workflow producer to finish, reconnect, and assert the final state and events are recoverable. Also persist and replay `workflow_failed`.

- [ ] **Step 5: Run API streaming tests**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/integration/api/test_message_stream.py tests/integration/api/test_sse_reconnect.py -v } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api backend/app/db/models/workflow.py backend/app/db/repositories backend/alembic/versions/0003_workflow_events.py backend/tests docs/api
git commit -m "feat: stream durable workflow events"
```

### Task 15: Human Feedback And Workflow Resume API

**Files:**
- Create: `backend/app/db/repositories/feedback.py`
- Create: `backend/app/workflow/outbox.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/db/models/workflow.py`
- Create: `backend/alembic/versions/0004_feedback_outbox.py`
- Create: `backend/app/api/v1/feedback.py`
- Modify: `backend/app/api/v1/router.py`
- Create: `backend/tests/integration/api/test_feedback.py`
- Create: `backend/tests/integration/api/test_feedback_idempotency.py`

- [ ] **Step 1: Write failing feedback validation tests**

Cover accepted, edited, and rejected actions; edited requires content, rejected requires reason, and a second identical request returns the original result. Add concurrent same-key requests, request fingerprints, and same-key/different-payload rejection.

- [ ] **Step 2: Implement feedback repository and endpoint**

Use `Idempotency-Key` plus a payload fingerprint and database uniqueness. Persist feedback, final solution, and a `resume_requested` outbox record in one transaction. `backend/app/workflow/outbox.py` implements a retryable worker that claims pending rows with a conditional status update or row lock, resumes the graph with the outbox ID as an idempotency command ID, and marks the row complete. Wire the worker into FastAPI lifespan startup with bounded polling and graceful shutdown so pending rows recover after process restart.

- [ ] **Step 3: Test conflicting second actions**

Submitting a different action after finalization returns HTTP 409 with `SESSION_ALREADY_FINALIZED`. Add failure-injection tests:

- after feedback commit but before graph resume;
- after graph resume/finalization but before marking the outbox row complete.

On retry, the graph/service detects the same command ID or already-finalized session, performs no duplicate finalization, and marks the outbox complete. Run two concurrent worker instances and assert only one claims a given row.

- [ ] **Step 4: Run feedback tests**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/integration/api/test_feedback.py tests/integration/api/test_feedback_idempotency.py -v } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/repositories/feedback.py backend/app/db/models/workflow.py backend/app/workflow/outbox.py backend/app/main.py backend/app/api/v1 backend/alembic/versions/0004_feedback_outbox.py backend/tests
git commit -m "feat: add human review feedback loop"
```

---

## Chunk 4: Frontend, Evaluation, And Deployment

### Task 16: Vue Workbench Foundation And Session State

**Files:**
- Create: `frontend/index.html`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/types/complaint.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/complaints.ts`
- Create: `frontend/src/api/sse.ts`
- Create: `frontend/src/stores/complaint.ts`
- Create: `frontend/src/views/ComplaintWorkbench.vue`
- Create: `frontend/tests/unit/complaint-store.test.ts`

- [ ] **Step 1: Install locked frontend dependencies**

Run: `Push-Location frontend; try { npm install; if ($LASTEXITCODE) { throw "npm install failed with exit code $LASTEXITCODE" } } finally { Pop-Location }`

Expected: `package-lock.json` is created and installation exits `0`.

- [ ] **Step 2: Write failing store tests**

Test session creation, workflow event reduction, streaming text accumulation, emotion/entities/validation state, replayed-event deduplication, out-of-order event rejection, `workflow_failed`, archive success, history restoration, final solution replacement, error state, and reset behavior.

- [ ] **Step 3: Run tests and verify failure**

Run: `Push-Location frontend; try { npm test -- complaint-store.test.ts; if ($LASTEXITCODE) { throw "Expected failing test observed" } } finally { Pop-Location }`

Expected: FAIL because the store does not exist.

- [ ] **Step 4: Implement typed API and Pinia store**

The store owns session state and event reduction. Components receive typed props and emit commands; they must not call APIs directly. `POST /messages` returns `run_id`; `src/api/sse.ts` consumes the GET event stream with `fetch()`, supports `AbortController`, sends `Last-Event-ID` on reconnect, and deduplicates by event ID.

- [ ] **Step 5: Create the workbench shell**

Use a restrained operational layout with stable left navigation, central work area, right evidence panel, and bottom feedback bar. Do not add a marketing landing page.

- [ ] **Step 6: Run unit and type checks**

Run: `Push-Location frontend; try { npm test; if ($LASTEXITCODE) { throw "Frontend tests failed with exit code $LASTEXITCODE" }; npm run type-check; if ($LASTEXITCODE) { throw "Type check failed with exit code $LASTEXITCODE" } } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend
git commit -m "feat: add complaint workbench state"
```

### Task 17: Workbench Components And Streaming Interaction

**Files:**
- Create: `frontend/src/components/SessionSidebar.vue`
- Create: `frontend/src/components/ComplaintComposer.vue`
- Create: `frontend/src/components/WorkflowTimeline.vue`
- Create: `frontend/src/components/SolutionPanel.vue`
- Create: `frontend/src/components/EvidencePanel.vue`
- Create: `frontend/src/components/FeedbackBar.vue`
- Modify: `frontend/src/views/ComplaintWorkbench.vue`
- Create: `frontend/tests/unit/ComplaintWorkbench.test.ts`
- Create: `frontend/tests/e2e/complaint-flow.spec.ts`
- Create: `frontend/playwright.config.ts`
- Create: `frontend/tests/mock-api/server.mjs`

- [ ] **Step 1: Write failing component integration test**

Mount the workbench with a mocked API, submit a complaint, emit staged SSE events, and assert intent, emotion, entities, evidence, streamed solution, validation results, risk notice, feedback actions, failure state, and archive success render.

- [ ] **Step 2: Implement accessible components**

Use semantic buttons, labels, keyboard focus, loading/error/empty states, and stable panel dimensions. Evidence items show source type, title, score, article number, and degradation notice. Session history can reload a completed or interrupted session from the API.

- [ ] **Step 3: Implement feedback interaction**

Accept submits directly; edit opens an editable solution area; reject requires a reason. Disable duplicate submission while pending.

- [ ] **Step 4: Write and run Playwright happy-path test**

Implement `frontend/tests/mock-api/server.mjs` with the session, message-start, SSE event, session-history, and feedback endpoints used by the browser tests. Configure Playwright `webServer` to start both Vite and this deterministic mock API so the command is self-contained.

Run: `Push-Location frontend; try { npm run test:e2e -- complaint-flow.spec.ts; if ($LASTEXITCODE) { throw "Playwright failed with exit code $LASTEXITCODE" } } finally { Pop-Location }`

Expected: complaint is submitted, streamed solution appears, evidence is visible, feedback succeeds, and finalized status is shown.

- [ ] **Step 5: Run frontend quality gates**

Run: `Push-Location frontend; try { npm test; if ($LASTEXITCODE) { throw "Frontend tests failed with exit code $LASTEXITCODE" }; npm run type-check; if ($LASTEXITCODE) { throw "Type check failed with exit code $LASTEXITCODE" }; npm run build; if ($LASTEXITCODE) { throw "Frontend build failed with exit code $LASTEXITCODE" } } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend
git commit -m "feat: complete complaint handling workbench"
```

### Task 18: Metrics And Offline Evaluation

**Files:**
- Create: `backend/app/observability/metrics.py`
- Create: `backend/app/evaluation/dataset.py`
- Create: `backend/app/evaluation/retrieval_metrics.py`
- Create: `backend/app/evaluation/business_metrics.py`
- Create: `backend/app/evaluation/performance.py`
- Create: `backend/app/evaluation/runner.py`
- Create: `backend/app/api/v1/metrics.py`
- Modify: `backend/app/api/v1/router.py`
- Create: `backend/scripts/run_evaluation.py`
- Create: `backend/tests/unit/evaluation/test_retrieval_metrics.py`
- Create: `backend/tests/unit/evaluation/test_business_metrics.py`
- Create: `backend/tests/performance/run_load.py`
- Create: `backend/tests/integration/api/test_metrics.py`
- Create: `data/evaluation/sample.jsonl`
- Create: `data/evaluation/acceptance.jsonl`
- Create: `docs/evaluation/README.md`

- [ ] **Step 1: Write failing metric tests**

Test intent accuracy, Recall@5, Top-3 hit rate, citation completeness, unsupported-claim ratio input validation, adoption rate, average handling time, API success rate, percentile calculation, and empty-dataset behavior.

- [ ] **Step 2: Implement pure metric functions**

Keep metric calculations deterministic and independent of model calls.

- [ ] **Step 3: Implement evaluation runner**

Record dataset version, model version, prompt version, knowledge version, workflow version, hardware note, and timestamps. Create a 120-case deidentified/synthetic acceptance dataset reviewed against the schema, with coverage labels for high-frequency, long-tail, dialect, missing-information, rule-conflict, and sensitive complaints. The small sample dataset is a smoke fixture only. Output JSON and Markdown summaries.

- [ ] **Step 4: Add Prometheus instrumentation**

Expose API latency, workflow node duration, retry count, degradation count, model time-to-first-token, and feedback actions. `/api/v1/metrics/summary` returns application-level summary data; `/metrics` exposes Prometheus format.

- [ ] **Step 5: Run evaluation and metric tests**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe -m pytest tests/unit/evaluation tests/integration/api/test_metrics.py -v; if ($LASTEXITCODE) { throw "Evaluation tests failed with exit code $LASTEXITCODE" } } finally { Pop-Location }`

Expected: PASS.

- [ ] **Step 6: Run sample evaluation**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe scripts/run_evaluation.py --dataset ../data/evaluation/sample.jsonl --mode smoke; if ($LASTEXITCODE) { throw "Smoke evaluation failed with exit code $LASTEXITCODE" } } finally { Pop-Location }`

Expected: versioned JSON and Markdown reports are created under `artifacts/evaluation/` and clearly labeled non-acceptance.

- [ ] **Step 7: Run acceptance evaluation**

Run: `Push-Location backend; try { ..\.venv\Scripts\python.exe scripts/run_evaluation.py --dataset ../data/evaluation/acceptance.jsonl --mode acceptance; if ($LASTEXITCODE) { throw "Acceptance evaluation failed with exit code $LASTEXITCODE" } } finally { Pop-Location }`

Expected: the runner validates exactly 120 labeled cases, reports all required coverage categories, and writes versioned acceptance reports.

- [ ] **Step 8: Add repeatable performance tests**

`backend/tests/performance/run_load.py` separately records API acceptance latency, retrieval latency, rerank latency, model time-to-first-token, generation rate, and end-to-end latency.

Run:

```powershell
Push-Location backend
try {
  ..\.venv\Scripts\python.exe tests/performance/run_load.py --base-url http://localhost:8000 --concurrency 50 --requests 500 --output artifacts/performance
  if ($LASTEXITCODE) { throw "Load test failed with exit code $LASTEXITCODE" }
} finally { Pop-Location }
```

Expected: JSON and Markdown reports include P50/P95/P99, error rate, environment, model/quantization, context length, and hardware. Fake mode cannot substantiate production throughput.

- [ ] **Step 9: Commit**

```bash
git add backend/app/observability backend/app/evaluation backend/app/api backend/scripts backend/tests data/evaluation docs/evaluation
git commit -m "feat: add observable evaluation pipeline"
```

### Task 19: Docker Compose And Production-Like Local Environment

**Files:**
- Modify: `docker-compose.yml`
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `infra/mysql/init.sql`
- Create: `infra/prometheus/prometheus.yml`
- Create: `backend/tests/stubs/model_server.py`
- Create: `docs/deployment/local.md`
- Create: `docs/deployment/private-models.md`
- Create: `backend/tests/contract/test_service_health.py`

- [ ] **Step 1: Write failing service configuration test**

Parse `docker-compose.yml` and assert required services exist: API, frontend, deterministic model stub, MySQL, Redis, Milvus, etcd, MinIO, Elasticsearch, Prometheus. Assert health-conditioned dependencies, named volumes, internal network exposure, and production profile settings. Keep real vLLM/Embedding/Rerank behind configurable external URLs so the default stack does not download models.

- [ ] **Step 2: Add container definitions and health checks**

Use named volumes, explicit networks, health checks, startup dependencies, non-root application containers, and environment variables from `.env`. Implement `backend/tests/stubs/model_server.py` as a deterministic HTTP service for LLM JSON/streaming, embedding, and rerank contracts; the Compose model-stub service runs this file for local integration only.

Pin Compose images to versions available within the timeline, including MySQL 8.0.x, Redis 7.2.x, Milvus 2.5.x, Elasticsearch 8.17.x, etcd 3.5.x, and a pre-cutoff MinIO release. Do not use `latest`.

Pin model artifacts as well: Qwen2.5-14B-Instruct, BGE-M3, and BGE-reranker must use an explicit repository revision or immutable local artifact checksum. Record model publication date, revision, quantization format, and conversion tool version.

- [ ] **Step 3: Document private model profiles**

Describe supported deployment profiles:

- Development: deterministic fake model gateway.
- Integration: external OpenAI-compatible test service.
- Production: private vLLM + BGE-M3 + BGE-reranker endpoints.

Include GPU memory, quantization, context length, batching, warmup, timeout, and load-test considerations without claiming unmeasured throughput. Add a production configuration test proving startup fails when private LLM, embedding, or reranker URLs are unset or use the fake scheme.

- [ ] **Step 4: Start infrastructure**

Run: `docker compose up -d --wait mysql redis etcd minio milvus elasticsearch prometheus`

Expected: all infrastructure health checks become healthy.

- [ ] **Step 5: Run infrastructure contracts**

Run:

```powershell
$env:RUN_INFRA_TESTS = "1"
Push-Location backend
try {
  ..\.venv\Scripts\python.exe -m pytest tests/contract -v
  if ($LASTEXITCODE) { throw "Infrastructure contracts failed with exit code $LASTEXITCODE" }
}
finally { Pop-Location; Remove-Item Env:RUN_INFRA_TESTS }
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml backend/Dockerfile frontend/Dockerfile infra docs/deployment backend/tests/stubs/model_server.py backend/tests/contract
git commit -m "ops: add production-like local stack"
```

### Task 20: End-To-End Verification And Delivery Documentation

**Files:**
- Create: `backend/tests/integration/test_end_to_end_complaint.py`
- Create: `frontend/tests/e2e/degraded-flow.spec.ts`
- Create: `scripts/verify.ps1`
- Create: `scripts/verify-stack.ps1`
- Create: `docs/evaluation/mvp-acceptance.md`
- Modify: `README.md`

- [ ] **Step 1: Write the backend end-to-end acceptance test**

Using deterministic fake model services and test search adapters:

1. Create a session.
2. Submit a complaint.
3. Assert intent and evidence events.
4. Assert solution citations reference returned evidence.
5. Assert human review is required.
6. Submit edited feedback.
7. Assert final persisted state.

- [ ] **Step 2: Write degraded-flow browser test**

Simulate Milvus degradation and assert the UI shows Elasticsearch-only status; simulate both retrieval stores failing and assert no generated solution is shown and the case is routed to manual handling. Add active-run reconnect, replay/live handoff, duplicate-event, and `workflow_failed` browser cases.

- [ ] **Step 3: Add one-command verification**

`scripts/verify.ps1` must run backend unit/integration tests and frontend unit/type/build checks. It must stop on the first failure and return a non-zero exit code.

`scripts/verify-stack.ps1` must start the complete Compose stack with `--wait`, run migrations, ingest sample knowledge into real Milvus and Elasticsearch, wire API/frontend to deterministic model endpoints, run contracts, run Playwright, execute the 50-concurrency load test, collect logs, and always stop the stack in a `finally` block. Every native command is followed by an exit-code check before cleanup.

- [ ] **Step 4: Run the full deterministic suite**

Run: `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`

Expected: backend tests PASS, frontend tests PASS, type-check PASS, production build PASS.

- [ ] **Step 5: Run the complete local-stack suite**

Run: `powershell -ExecutionPolicy Bypass -File scripts/verify-stack.ps1`

Expected: real Milvus + Elasticsearch hybrid retrieval, API/frontend, reconnect behavior, infrastructure contracts, and Playwright tests PASS; the stack is removed afterward even on failure.

- [ ] **Step 6: Complete acceptance report**

Record test dataset version, model mode, hardware, measured latency, retrieval metrics, citation completeness, known limitations, and all deviations from the targets in the spec. Do not claim production concurrency from fake-model tests.

The report must include a dependency provenance table with package/image version and release date, and fail the release audit if any runtime dependency was first published after 2026-04-30.

- [ ] **Step 7: Final verification**

Run:

```bash
git status --short
git log --oneline --decorate -20
```

Expected: only intentional documentation/report artifacts are uncommitted; task commits are visible and ordered.

- [ ] **Step 8: Commit**

```bash
git add backend/tests frontend/tests scripts docs/evaluation README.md
git commit -m "test: verify suzhida mvp workflow"
```

---

## Execution Notes

- Use `$subagent-driven-development` for execution because Codex subagents are available. Each task gets a fresh implementation worker followed by specification and code-quality review.
- Use `$test-driven-development` for every behavior change: write the failing test, observe the intended failure, implement the minimum, and rerun.
- Use `$systematic-debugging` whenever a test fails for an unexpected reason; do not patch around symptoms.
- Use `$requesting-code-review` after each task and `$verification-before-completion` before declaring a chunk complete.
- Do not start LoRA fine-tuning, production Kubernetes work, automatic case closure, or a multi-agent redesign during this MVP plan.
- Keep production services replaceable through typed gateways. Unit and deterministic integration tests must not require external network access or GPU hardware.
- Any measured performance claim must include hardware, model/quantization, dataset, concurrency, context length, and test command.
- Treat LangGraph 1.0.5 as a late-project upgrade from the 0.4.x line; migration notes must not claim 1.x was used before its release.
- Do not use APIs introduced after the pinned versions, even when current documentation recommends them.
