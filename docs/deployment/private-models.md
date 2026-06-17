# Private Model Profiles

## Development

- Uses the deterministic model stub.
- No external model downloads.
- Best for repeatable local tests and UI development.

## Integration

- Uses an OpenAI-compatible internal test service or the local stub.
- Matches the production API shape without production load requirements.

## Single-Machine Local GPU

Recommended for functional testing on a 12 GB VRAM workstation.

- LLM: `Qwen2.5-7B-Instruct`
- Quantization: INT4 artifact family already validated in your private registry
- Runtime: private vLLM endpoint
- Context length: start at 4096
- `max_num_seqs`: start at `4`, increase to `8` only after measuring headroom
- GPU memory utilization target: `0.85` to `0.90`
- Warmup: send at least one short request after process start
- Timeouts: keep API `llm_timeout=60`, embedding/reranker `30`
- Embedding and reranker: keep as independent endpoints; CPU hosting is acceptable for local verification

This profile is for end-to-end correctness only. Do not use it to claim production concurrency.

## Production

Recommended for private deployment on A10-class GPU nodes.

- LLM: `Qwen2.5-14B-Instruct`
- Quantization: INT4 if validated for your artifact revision; otherwise use the lowest-memory format you have benchmarked and approved
- Runtime: private vLLM endpoint
- Context length: start at 4096 or 8192 depending on measured KV-cache headroom
- Continuous batching: enabled
- `max_num_seqs`: start conservatively and tune from measured P95 latency, not theory
- Embedding: `BAAI/bge-m3`
- Reranker: `BAAI/bge-reranker-v2-m3`
- Keep `LLM_BASE_URL`, `EMBEDDING_BASE_URL`, and `RERANKER_BASE_URL` non-empty and non-fake

Artifact governance to record per release:

- model name
- publication date
- repository revision or immutable checksum
- quantization format
- conversion/export tool version

Load-test notes:

- Report hardware, quantization, dataset, concurrency, context length, and command line with every throughput claim.
- Do not extrapolate 200-way concurrency from fake-model, single-node, or smoke-test results.
- Treat embedding and reranker saturation independently from LLM saturation.

The application must fail fast if production URLs are missing or use a fake scheme.
