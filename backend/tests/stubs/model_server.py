from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse


app = FastAPI(title="suzhida-model-stub")


def _is_service_impact_economic_loss(text: str) -> bool:
    return "网络" in text and "赔偿" in text and ("损失" in text or "炒股" in text)


def _intent_payload(user_text: str) -> dict[str, Any]:
    if _is_service_impact_economic_loss(user_text):
        return {
            "intent": "service_impact_economic_loss",
            "emotion": "anxious",
            "entities": {"product": "网络服务", "topic": "economic_loss"},
            "confidence": 0.96,
            "risk_level": "high",
        }
    return {
        "intent": "billing_dispute",
        "emotion": "angry",
        "entities": {"product": "套餐", "topic": "扣费"},
        "confidence": 0.93,
        "risk_level": "medium",
    }


def _solution_payload(user_text: str) -> dict[str, Any]:
    if _is_service_impact_economic_loss(user_text):
        return {
            "solution_text": (
                "该投诉归入 service impact and economic loss 高风险诉求，"
                "需先核查服务异常时段、影响范围和损失主张材料，再升级至资深人工复核。"
            ),
            "assessment": "涉及服务影响用户生产经营并引发经济损失，属于高风险投诉，需要人工复核。",
            "steps": [
                "核查故障告警与修复记录",
                "确认用户受影响时段与业务号码",
                "收集损失主张材料后转资深人工复核",
            ],
            "risk_notice": "在人工审批前不得直接承诺赔付款项，必要时转法务支持。",
            "validation_status": "passed",
            "recommended_route": "senior_human_review",
        }
    return {
        "solution_text": "建议核查套餐扣费并在下期账单退回差额。",
        "assessment": "证据充分，可以进入人工复核。",
        "steps": ["核查账单", "确认扣费来源", "执行退费"],
        "risk_notice": "涉及账单修正，需要人工审核。",
        "validation_status": "passed",
        "recommended_route": "human_review",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat/completions")
async def chat_completions(payload: dict[str, Any]) -> Any:
    if payload.get("stream"):
        return await chat_completions_stream(payload)

    messages = payload.get("messages", [])
    system_prompt = str(messages[0]["content"]) if messages else ""
    last_message = str(messages[-1]["content"]) if messages else ""

    if payload.get("response_format", {}).get("type") == "json_object":
        if "intent classification" in system_prompt:
            content = json.dumps(_intent_payload(last_message), ensure_ascii=False)
        else:
            content = json.dumps(_solution_payload(last_message), ensure_ascii=False)
    else:
        content = f"Stub response for: {last_message}"

    return {
        "id": "chatcmpl-stub",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
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
            "choices": [{"delta": {"content": f"Stub response for: {message}"}}]
        }
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
