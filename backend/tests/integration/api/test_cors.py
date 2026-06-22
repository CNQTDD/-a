def test_cors_allows_frontend_preview_origin(client) -> None:
    response = client.options(
        "/api/v1/complaints/sessions",
        headers={
            "Origin": "http://127.0.0.1:5299",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5299"
    assert "POST" in response.headers["access-control-allow-methods"]
