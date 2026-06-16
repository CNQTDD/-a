from __future__ import annotations


def test_metrics_summary_endpoint_returns_metrics_payload(client) -> None:
    response = client.get("/api/v1/metrics/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "suzhida-api"
    assert "retrieval" in payload
    assert "evaluation" in payload


def test_prometheus_metrics_endpoint_exposes_text_payload(client) -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
