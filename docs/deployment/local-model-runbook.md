# Local Model Runbook

This runbook is for the single-machine test path where the infrastructure stack stays in Docker Compose and the private model services run on the Windows host.

Target machine profile:

- 32 GB system RAM
- 12 GB VRAM class GPU
- local functional verification
- low concurrency only

Recommended model split:

- LLM: `Qwen2.5-7B-Instruct`
- embedding: `BAAI/bge-m3`
- reranker: `BAAI/bge-reranker-v2-m3`

## 1. Endpoint Contract

The application expects three HTTP endpoints.

### LLM endpoint

Base URL example:

```text
http://127.0.0.1:8001/v1
```

Required request:

```json
{
  "model": "Qwen2.5-7B-Instruct",
  "messages": [
    {"role": "system", "content": "intent classification"},
    {"role": "user", "content": "The customer says the plan was billed twice and requests a refund."}
  ],
  "response_format": {"type": "json_object"}
}
```

Required response shape:

```json
{
  "choices": [
    {
      "message": {
        "content": "{\"intent\":\"billing_dispute\"}"
      }
    }
  ]
}
```

Streaming is OpenAI-style SSE on the same `/v1/chat/completions` route with `"stream": true`.

### Embedding endpoint

Base URL example:

```text
http://127.0.0.1:8002/v1
```

Required request:

```json
{
  "model": "BAAI/bge-m3",
  "input": ["double billing complaint", "refund process"]
}
```

Required response shape:

```json
{
  "data": [
    {"index": 0, "embedding": [0.1, 0.2, 0.3]},
    {"index": 1, "embedding": [0.1, 0.2, 0.3]}
  ]
}
```

### Reranker endpoint

Base URL example:

```text
http://127.0.0.1:8003/v1
```

Required request:

```json
{
  "model": "BAAI/bge-reranker-v2-m3",
  "query": "double billing complaint",
  "documents": ["billing policy article", "refund process article"]
}
```

Accepted response shapes:

```json
{"scores": [0.9, 0.4]}
```

or

```json
{
  "results": [
    {"index": 0, "score": 0.9},
    {"index": 1, "score": 0.4}
  ]
}
```

## 2. Host Startup Recommendation

This repository does not bundle real model weights. Use your private artifacts and your approved internal startup commands.

### LLM

Use a private vLLM OpenAI-compatible server on port `8001`.

Recommended starting point for this workstation:

- model: `Qwen2.5-7B-Instruct`
- quantization: INT4
- context length: `4096`
- `max_num_seqs`: `4`
- GPU memory utilization: `0.85` to `0.90`

Warm up the model with one short JSON request before connecting the API stack.

### Embedding

Serve `BAAI/bge-m3` on port `8002` with a `/v1/embeddings` route matching the contract above.

For this machine, CPU service is acceptable if GPU memory is tight.

### Reranker

Serve `BAAI/bge-reranker-v2-m3` on port `8003` with a `/v1/rerank` route matching the contract above.

For this machine, CPU service is acceptable if GPU memory is tight.

## 3. Environment File

Start from [`.env.local-gpu.example`](D:\项目\suzhida\.env.local-gpu.example).

Critical values:

```text
LLM_BASE_URL=http://host.docker.internal:8001/v1
EMBEDDING_BASE_URL=http://host.docker.internal:8002/v1
RERANKER_BASE_URL=http://host.docker.internal:8003/v1
LLM_MODEL=Qwen2.5-7B-Instruct
EMBEDDING_MODEL=BAAI/bge-m3
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
```

## 4. Preflight Checks

Run these from the Windows host before starting Compose.

### LLM JSON check

```powershell
$body = @{
  model = "Qwen2.5-7B-Instruct"
  messages = @(
    @{ role = "system"; content = "intent classification" }
    @{ role = "user"; content = "The plan was billed twice. Please investigate and refund the extra charge." }
  )
  response_format = @{ type = "json_object" }
} | ConvertTo-Json -Depth 6

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/v1/chat/completions" -ContentType "application/json" -Body $body
```

### Embedding check

```powershell
$body = @{
  model = "BAAI/bge-m3"
  input = @("double billing complaint", "billing review")
} | ConvertTo-Json -Depth 4

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8002/v1/embeddings" -ContentType "application/json" -Body $body
```

### Reranker check

```powershell
$body = @{
  model = "BAAI/bge-reranker-v2-m3"
  query = "double billing complaint"
  documents = @("billing policy article", "refund process article")
} | ConvertTo-Json -Depth 4

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8003/v1/rerank" -ContentType "application/json" -Body $body
```

## 5. Start Compose Stack

Do not start `model-stub` in this mode.

```powershell
docker compose --profile development up -d --wait api frontend mysql redis etcd minio milvus elasticsearch prometheus
```

## 6. Initialize The Application

### Run migrations

```powershell
docker compose exec -T api alembic upgrade head
```

### Seed sample knowledge

```powershell
docker compose exec -T api python scripts/seed_sample_knowledge.py `
  --database-url mysql+pymysql://suzhida:suzhida@mysql:3306/suzhida `
  --elasticsearch-url http://elasticsearch:9200 `
  --milvus-uri http://milvus:19530
```

## 7. Smoke Verification

### API health

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/health"
```

Expected:

```json
{"service":"suzhida-api","status":"ok"}
```

### Frontend

Open:

```text
http://127.0.0.1:5280
```

Submit one billing complaint and verify:

1. the timeline advances
2. evidence appears in the right panel
3. a generated solution is returned
4. the case ends in human review, not silent auto-close

## 8. OOM Recovery Order

If the machine becomes unstable, reduce load in this order:

1. lower `max_num_seqs`
2. reduce LLM context length
3. move embedding to CPU
4. move reranker to CPU
5. stop Prometheus during local manual testing

Do not shrink Elasticsearch heap below the current baseline unless you measure a real need.

## 9. Stop The Stack

```powershell
docker compose down --remove-orphans
```
