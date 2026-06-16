class TestTracing:
    """Verify trace ID propagation through the system."""

    def test_error_envelope_contains_same_trace_id(self, client):
        """The error response trace_id should match the request's trace ID."""
        response = client.get(
            "/api/v1/complaints/sessions/nonexistent-id",
            headers={"X-Request-ID": "my-trace-123"},
        )
        assert response.status_code == 404
        body = response.json()
        assert body["trace_id"] == "my-trace-123"


class TestErrorEnvelope:
    """Verify the unified error envelope format."""

    def test_unknown_route_returns_error_envelope(self, client):
        response = client.get("/api/v1/unknown-endpoint")
        assert response.status_code == 404
        body = response.json()
        assert "code" in body
        assert "message" in body
        assert "trace_id" in body

    def test_error_code_is_machine_readable(self, client):
        response = client.get("/api/v1/complaints/sessions/nonexistent-id")
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "NOT_FOUND"
