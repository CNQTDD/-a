# Suzhida

Suzhida is a complaint intelligence and closed-loop handling MVP built around a single-agent LangGraph workflow, hybrid retrieval, and a Vue workbench.

## Local Development

- Compose API: `http://127.0.0.1:8000`
- Compose frontend workbench: `http://127.0.0.1:5280`
- Vite dev server: `http://127.0.0.1:4173`
- Deterministic mock model API for browser tests: `http://127.0.0.1:5184`

## Verification

- `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`
- `powershell -ExecutionPolicy Bypass -File scripts/verify-stack.ps1`

The deterministic verification path uses local fakes and the compose-backed stack verification path exercises MySQL, Redis, etcd, MinIO, Milvus, Elasticsearch, the API, and the frontend.

For host-served real-model testing, see [D:\项目\suzhida\docs\deployment\local-model-runbook.md](D:\项目\suzhida\docs\deployment\local-model-runbook.md).

## Notes

- Production inference is intended to use private vLLM, embedding, and reranker endpoints.
- Local tests use deterministic fakes and mock services where appropriate.
- For local real-model testing on a single 12 GB GPU, use `Qwen2.5-7B-Instruct` with INT4 artifacts and keep embedding/reranker services lightweight.
- Sample evaluation reports are stored under `docs/evaluation/`.
