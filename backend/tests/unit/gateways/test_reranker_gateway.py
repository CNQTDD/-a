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
    from app.gateways.reranker import RerankerGateway

    return RerankerGateway(
        base_url="http://gateway.local",
        model="demo-reranker",
        transport=transport,
        max_retries=max_retries,
    )


@pytest.mark.asyncio
async def test_reranker_gateway_retries_one_timeout() -> None:
    transport = SequencedTransport(
        [
            httpx.ReadTimeout("timeout", request=httpx.Request("POST", "http://x")),
            _json_response({"scores": [0.9, 0.1]}),
        ]
    )
    gateway = build_gateway(httpx.MockTransport(transport), max_retries=1)

    result = await gateway.rerank(
        query="投诉费用异常",
        documents=["文档一", "文档二"],
        request_id="req-rerank-1",
    )

    assert result == [0.9, 0.1]
    assert transport.calls == 2


@pytest.mark.asyncio
async def test_reranker_gateway_distinguishes_empty_results_from_outage() -> None:
    transport = SequencedTransport([_json_response({"scores": []})])
    gateway = build_gateway(httpx.MockTransport(transport))

    result = await gateway.rerank(
        query="投诉费用异常",
        documents=[],
        request_id="req-rerank-2",
    )

    assert result == []
    assert transport.calls == 1


@pytest.mark.asyncio
async def test_reranker_gateway_exhausts_retry_on_5xx() -> None:
    transport = SequencedTransport(
        [
            _json_response({"error": "bad gateway"}, 503),
            _json_response({"error": "still bad"}, 503),
        ]
    )
    gateway = build_gateway(httpx.MockTransport(transport), max_retries=1)

    with pytest.raises(Exception):
        await gateway.rerank(
            query="投诉费用异常",
            documents=["文档一"],
            request_id="req-rerank-3",
        )

    assert transport.calls == 2


@pytest.mark.asyncio
async def test_reranker_gateway_logs_sanitized_audit(
    caplog: pytest.LogCaptureFixture,
) -> None:
    transport = SequencedTransport([_json_response({"scores": [0.7]})])
    gateway = build_gateway(httpx.MockTransport(transport))
    caplog.set_level(logging.INFO)

    await gateway.rerank(
        query="电话13812345678 身份证530102199001011234 邮箱user@example.com",
        documents=["云南省昆明市五华区人民中路100号"],
        request_id="req-rerank-4",
    )

    rendered = "\n".join(record.getMessage() for record in caplog.records)
    assert "13812345678" not in rendered
    assert "530102199001011234" not in rendered
    assert "user@example.com" not in rendered
    assert "gateway_audit" in rendered
