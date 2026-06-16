from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse


app = FastAPI(title="suzhida-model-stub")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat/completions")
async def chat_completions(payload: dict[str, Any]) -> dict[str, Any]:
    messages = payload.get("messages", [])
    last_message = messages[-1]["content"] if messages else ""
    return {
        "id": "chatcmpl-stub",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"Stub response for: {last_message}",
                },
                "finish_reason": "stop",
            }
        ],
    }


@app.post("/v1/embeddings")
async def embeddings(payload: dict[str, Any]) -> dict[str, Any]:
    inputs = payload.get("input", [])
    if isinstance(inputs, str):
        inputs = [inputs]
    return {
        "object": "list",
        "data": [
            {"index": index, "embedding": [0.1, 0.2, 0.3]}
            for index, _ in enumerate(inputs)
        ],
        "model": payload.get("model", "stub"),
    }


@app.post("/v1/rerank")
async def rerank(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": payload.get("model", "stub"),
        "results": [
            {"index": index, "score": 1.0 / (index + 1)}
            for index, _ in enumerate(payload.get("documents", []))
        ],
    }


@app.post("/v1/chat/completions/stream")
async def chat_completions_stream(payload: dict[str, Any]) -> StreamingResponse:
    message = payload.get("messages", [{}])[-1].get("content", "")

    async def event_stream() -> Any:
        yield f"data: {message}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
