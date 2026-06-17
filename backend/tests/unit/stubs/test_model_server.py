from __future__ import annotations

from fastapi.testclient import TestClient

from tests.stubs.model_server import app


def test_model_stub_returns_json_content_for_gateway_style_chat_requests() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "demo-model",
            "messages": [
                {"role": "system", "content": "intent classification"},
                {"role": "user", "content": "套餐扣费有误"},
            ],
            "response_format": {"type": "json_object"},
        },
    )

    assert response.status_code == 200
    content = response.json()["choices"][0]["message"]["content"]
    assert content.startswith("{")
    assert "intent" in content


def test_model_stub_returns_readable_solution_text_for_generation_requests() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "demo-model",
            "messages": [
                {"role": "system", "content": "solution generation"},
                {"role": "user", "content": "Please produce a handling plan."},
            ],
            "response_format": {"type": "json_object"},
        },
    )

    assert response.status_code == 200
    content = response.json()["choices"][0]["message"]["content"]
    assert "建议核查套餐扣费" in content


def test_model_stub_streams_openai_style_sse_chunks() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "demo-model",
            "messages": [{"role": "user", "content": "请生成处理建议"}],
            "stream": True,
        },
    )

    assert response.status_code == 200
    assert 'data: {"choices":' in response.text
    assert "data: [DONE]" in response.text
