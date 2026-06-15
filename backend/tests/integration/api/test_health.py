def test_health_returns_service_status(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"service": "suzhida-api", "status": "ok"}
