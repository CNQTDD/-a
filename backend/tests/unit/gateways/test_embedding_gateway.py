from __future__ import annotations

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
    from app.gateways.embeddings import EmbeddingGateway

    return EmbeddingGateway(
        base_url="http://gateway.local",
        model="demo-embedding",
        transport=transport,
        max_retries=max_retries,
    )


@pytest.mark.asyncio
async def test_embedding_gateway_retries_one_timeout() -> None:
    transport = SequencedTransport(
        [
            httpx.ReadTimeout("timeout", request=httpx.Request("POST", "http://x")),
            _json_response({"data": [{"embedding": [0.1, 0.2]}]}),
        ]
    )
    gateway = build_gateway(httpx.MockTransport(transport), max_retries=1)

    result = await gateway.embed_texts(["投诉文本"], request_id="req-emb-1")

    assert result == [[0.1, 0.2]]
    assert transport.calls == 2


@pytest.mark.asyncio
async def test_embedding_gateway_raises_on_malformed_response() -> None:
    transport = SequencedTransport([_json_response({"data": []})])
    gateway = build_gateway(httpx.MockTransport(transport))

    with pytest.raises(Exception):
        await gateway.embed_texts(["投诉文本"], request_id="req-emb-2")

    assert transport.calls == 1


@pytest.mark.asyncio
async def test_embedding_gateway_does_not_retry_4xx() -> None:
    transport = SequencedTransport([_json_response({"error": "bad request"}, 400)])
    gateway = build_gateway(httpx.MockTransport(transport), max_retries=1)

    with pytest.raises(Exception):
        await gateway.embed_texts(["投诉文本"], request_id="req-emb-3")

    assert transport.calls == 1


@pytest.mark.asyncio
async def test_embedding_gateway_logs_sanitized_audit(
    caplog: pytest.LogCaptureFixture,
) -> None:
    transport = SequencedTransport(
        [_json_response({"data": [{"embedding": [0.1, 0.2]}]})]
    )
    gateway = build_gateway(httpx.MockTransport(transport))
    caplog.set_level(logging.INFO)

    await gateway.embed_texts(
        ["电话13812345678 身份证530102199001011234 邮箱user@example.com"],
        request_id="req-emb-4",
    )

    rendered = "\n".join(record.getMessage() for record in caplog.records)
    assert "13812345678" not in rendered
    assert "530102199001011234" not in rendered
    assert "user@example.com" not in rendered
    assert "gateway_audit" in rendered
