# Local Deployment

The local deployment path has two supported modes:

1. Deterministic verification mode
2. Single-machine real-model mode

The deterministic mode is the default because it is fast, repeatable, and does not download private model artifacts.

## Mode 1: Deterministic Verification

Services included:

- API
- Frontend
- Deterministic model stub
- MySQL
- Redis
- Milvus
- etcd
- MinIO
- Elasticsearch
- Prometheus

Run:

```powershell
docker compose --profile development up -d --wait api frontend model-stub mysql redis etcd minio milvus elasticsearch prometheus
```

This is the path used by `scripts/verify-stack.ps1`.

## Mode 2: Single-Machine Real-Model Testing

This mode keeps the Compose infrastructure stack and replaces the model stub with private host-served endpoints.

Recommended host assumptions:

- System RAM: 32 GB
- GPU VRAM: 12 GB
- CPU: high-core mobile/desktop class
- Expected use: functional verification and low-concurrency operator testing, not production throughput claims

Recommended resource split for this machine:

- Docker Desktop memory: 14 GB to 16 GB
- Docker Desktop CPUs: 10 to 12
- Leave at least 12 GB host RAM free for Windows, vLLM, embedding, reranker, and browser tooling

Recommended stack split:

- Docker Compose: MySQL, Redis, etcd, MinIO, Milvus, Elasticsearch, Prometheus, API, frontend
- Host process: vLLM serving `Qwen2.5-7B-Instruct`
- Host process: embedding endpoint for `BAAI/bge-m3`
- Host process: reranker endpoint for `BAAI/bge-reranker-v2-m3`

Do not run the default `model-stub` container in this mode.

### Environment setup

Use `.env.local-gpu.example` as the starting point. The key detail is that the API container must call back to host-served model endpoints through `host.docker.internal`.

Required endpoint values:

- `LLM_BASE_URL=http://host.docker.internal:8001/v1`
- `EMBEDDING_BASE_URL=http://host.docker.internal:8002/v1`
- `RERANKER_BASE_URL=http://host.docker.internal:8003/v1`

### Compose startup

```powershell
docker compose --profile development up -d --wait api frontend mysql redis etcd minio milvus elasticsearch prometheus
```

### Validation order

1. Start the private model services on the host.
2. Check the model health endpoints manually.
3. Start the Compose infrastructure and application services.
4. Run Alembic migrations.
5. Seed sample knowledge.
6. Open `http://127.0.0.1:5280` and submit a complaint.

Detailed step-by-step instructions are in [D:\项目\suzhida\docs\deployment\local-model-runbook.md](D:\项目\suzhida\docs\deployment\local-model-runbook.md).

### Practical OOM guidance

- Keep Elasticsearch at the current `512m` heap unless a measured need appears.
- Do not load `Qwen2.5-14B` onto a 12 GB card for this local profile.
- Prefer INT4 inference artifacts for the 7B local model.
- Keep local test context length at 4096 unless a larger window is required for a specific case.
- Keep local concurrent generation low, typically `max_num_seqs=4` to `8`, until measured otherwise.
- If the GPU is saturated, move embedding and reranker to CPU service processes before reducing Milvus or Elasticsearch memory further.
