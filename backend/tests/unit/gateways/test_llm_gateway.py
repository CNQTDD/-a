from __future__ import annotations

import json
import logging

import httpx
import pytest


class SequencedTransport:
    def __init__(self, actions: list[object]):
        self.actions = actions
        self.calls = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        action = self.actions[min(self.calls - 1, len(self.actions) - 1)]
        if isinstance(action, Exception):
            raise action
        return action


def _json_response(
    payload: dict[str, object], status_code: int = 200
) -> httpx.Response:
    return httpx.Response(status_code, json=payload)


def build_gateway(transport: httpx.MockTransport, max_retries: int = 0):
    from app.gateways.llm import LLMGateway

    return LLMGateway(
        base_url="http://gateway.local",
        model="demo-model",
        transport=transport,
        max_retries=max_retries,
    )


@pytest.mark.asyncio
async def test_llm_gateway_retries_one_timeout() -> None:
    transport = SequencedTransport(
        [
            httpx.ReadTimeout("timeout", request=httpx.Request("POST", "http://x")),
            _json_response(
                {
                    "choices": [
                        {"message": {"content": json.dumps({"intent": "billing"})}}
                    ],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                }
            ),
        ]
    )
    gateway = build_gateway(httpx.MockTransport(transport), max_retries=1)

    result = await gateway.complete_json(
        messages=[{"role": "user", "content": "test"}],
        request_id="req-llm-1",
    )

    assert result == {"intent": "billing"}
    assert transport.calls == 2


@pytest.mark.asyncio
async def test_llm_gateway_does_not_retry_bad_request() -> None:
    transport = SequencedTransport([_json_response({"error": "bad request"}, 400)])
    gateway = build_gateway(httpx.MockTransport(transport), max_retries=1)

    with pytest.raises(Exception):
        await gateway.complete_json(
            messages=[{"role": "user", "content": "test"}],
            request_id="req-llm-2",
        )

    assert transport.calls == 1


@pytest.mark.asyncio
async def test_llm_gateway_streams_text_chunks() -> None:
    body = (
        'data: {"choices":[{"delta":{"content":"hello "}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"world"}}]}\n\n'
        "data: [DONE]\n\n"
    )
    transport = SequencedTransport(
        [
            httpx.Response(
                200, headers={"content-type": "text/event-stream"}, content=body
            )
        ]
    )
    gateway = build_gateway(httpx.MockTransport(transport))

    chunks: list[str] = []
    async for chunk in gateway.stream_completion(
        messages=[{"role": "user", "content": "stream"}],
        request_id="req-llm-3",
    ):
        chunks.append(chunk)

    assert "".join(chunks) == "hello world"
    assert transport.calls == 1


@pytest.mark.asyncio
async def test_llm_gateway_logs_sanitized_audit(
    caplog: pytest.LogCaptureFixture,
) -> None:
    transport = SequencedTransport(
        [
            _json_response(
                {
                    "choices": [{"message": {"content": json.dumps({"ok": True})}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                }
            )
        ]
    )
    gateway = build_gateway(httpx.MockTransport(transport))
    caplog.set_level(logging.INFO)

    await gateway.complete_json(
        messages=[
            {
                "role": "user",
                "content": (
                    "电话13812345678 身份证530102199001011234 "
                    "邮箱user@example.com"
                ),
            }
        ],
        request_id="req-llm-4",
    )

    rendered = "\n".join(record.getMessage() for record in caplog.records)
    assert "13812345678" not in rendered
    assert "530102199001011234" not in rendered
    assert "user@example.com" not in rendered
    assert "gateway_audit" in rendered
