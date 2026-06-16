# Local Deployment

The local Compose stack is intended for development and integration testing.

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

The default stack uses the deterministic model stub so we can verify the workflow without downloading production models.

For production-like runs, provide private `LLM_BASE_URL`, `EMBEDDING_BASE_URL`, and `RERANKER_BASE_URL` values that point to internal services.
