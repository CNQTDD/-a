from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse


app = FastAPI(title="suzhida-model-stub")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat/completions")
async def chat_completions(payload: dict[str, Any]) -> Any:
    if payload.get("stream"):
        return await chat_completions_stream(payload)

    messages = payload.get("messages", [])
    system_prompt = str(messages[0]["content"]) if messages else ""
    last_message = messages[-1]["content"] if messages else ""

    if payload.get("response_format", {}).get("type") == "json_object":
        if "intent classification" in system_prompt:
            content = json.dumps(
                {
                    "intent": "billing_dispute",
                    "emotion": "angry",
                    "entities": {"product": "套餐", "topic": "扣费"},
                    "confidence": 0.93,
                    "risk_level": "medium",
                },
                ensure_ascii=False,
            )
        else:
            content = json.dumps(
                {
                    "solution_text": "建议核查套餐扣费并在下期账单退回差额。",
                    "assessment": "证据充分，可以进入人工复核。",
                    "steps": ["核查账单", "确认扣费来源", "执行退回"],
                    "risk_notice": "涉及账单修正，需要人工审核。",
                    "validation_status": "passed",
                    "recommended_route": "human_review",
                },
                ensure_ascii=False,
            )
    else:
        content = f"Stub response for: {last_message}"

    return {
        "id": "chatcmpl-stub",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
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
        chunk = {
            "choices": [
                {
                    "delta": {
                        "content": f"Stub response for: {message}",
                    }
                }
            ]
        }
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
