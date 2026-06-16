# Suzhida MVP Acceptance Report

## Scope

This report documents the end-to-end verification path for the MVP plan:

- backend unit and integration tests
- frontend unit, type, and build checks
- compose-backed stack verification
- backend acceptance flow
- frontend degraded-flow browser coverage
- repeatable load test output

## Verification Commands

- `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`
- `powershell -ExecutionPolicy Bypass -File scripts/verify-stack.ps1`

## Outcome

- `verify.ps1` passed fresh on 2026-06-16.
- `verify-stack.ps1` passed fresh on 2026-06-16.
- Backend acceptance flow passed.
- Frontend degraded-flow browser coverage passed.
- Load test completed and wrote `backend/artifacts/performance/performance.json` and `backend/artifacts/performance/performance.md`.

## Performance Summary

- Environment: local
- Base URL: `http://127.0.0.1:8000`
- Concurrency: 50
- Requests: 500
- Model: `Qwen2.5-14B-Instruct (INT4)`
- Context length: 8192
- Hardware: `local-dev`
- Error rate: 0.0000
- API latency P50/P95/P99: 0.0691 / 0.0848 / 0.0926 seconds

## Acceptance Notes

- Dataset version for offline evaluation: `data/evaluation/acceptance.jsonl`
- Sample knowledge seed data: `data/samples/complaints.jsonl` and `data/samples/rules.md`
- Citation completeness: the acceptance flow asserted that cited evidence IDs were present and persisted with the solution.
- Known limitations: local-dev throughput is not a production claim; the stack emits a small number of deprecation warnings from existing UTC datetime usage.

## Provenance

The stack verification used the pinned runtime versions from the implementation plan, including:

- Python 3.11.x
- FastAPI 0.115.12
- Pydantic 2.11.5
- SQLAlchemy 2.0.41
- LangGraph 1.0.5
- PyMilvus 2.5.10 / Milvus 2.5.x
- Elasticsearch 8.17.2 / 8.17.x
- Redis 5.2.1 / 7.2.x
- httpx 0.28.1
- Vue 3.5.13
- Pinia 2.3.1
- Vite 6.1.x
- TypeScript 5.7.x
- Vitest 3.0.x
- Playwright 1.50.x

All runtime dependencies used in this rebuild were selected from the pre-2026-04-30 compatibility baseline in the implementation plan.
