# Private Model Profiles

## Development

- Uses the deterministic model stub.
- No external model downloads.
- Best for repeatable local tests and UI development.

## Integration

- Uses an OpenAI-compatible internal test service or the local stub.
- Matches the production API shape without production load requirements.

## Production

- Uses private vLLM, BGE-M3 embedding, and BGE-reranker endpoints inside the internal network.
- Keep `LLM_BASE_URL`, `EMBEDDING_BASE_URL`, and `RERANKER_BASE_URL` non-empty and non-fake.
- Tune context length, batching, timeout, and GPU memory per deployment.

The application must fail fast if production URLs are missing or use a fake scheme.
