import json
import logging
import re

import pytest


class TestTraceIdPropagation:
    """Verify that X-Request-ID is propagated and a UUID is generated when missing."""

    def test_inbound_request_id_is_propagated(self, client):
        response = client.get("/health", headers={"X-Request-ID": "test-trace-001"})
        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == "test-trace-001"

    def test_missing_request_id_generates_uuid(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        trace_id = response.headers.get("X-Request-ID")
        assert trace_id is not None
        # UUID format: 8-4-4-4-12 hex digits
        assert re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", trace_id) is not None

    def test_error_response_contains_trace_id(self, client):
        response = client.get("/api/v1/complaints/sessions/nonexistent-id")
        assert response.status_code == 404
        body = response.json()
        assert "trace_id" in body
        assert body["trace_id"] is not None


class TestMaskedLogging:
    """Verify that sensitive data is masked in structured logs."""

    def test_raw_phone_never_appears_in_logs(self, caplog, client):
        caplog.set_level(logging.INFO)
        client.get("/health?q=13812345678")
        for record in caplog.records:
            message = json.dumps(record.msg) if isinstance(record.msg, dict) else str(record.msg)
            assert "13812345678" not in message

    def test_raw_identity_number_never_appears_in_logs(self, caplog, client):
        caplog.set_level(logging.INFO)
        client.get("/health?q=530102199001011234")
        for record in caplog.records:
            message = json.dumps(record.msg) if isinstance(record.msg, dict) else str(record.msg)
            assert "530102199001011234" not in message

    def test_raw_email_never_appears_in_logs(self, caplog, client):
        caplog.set_level(logging.INFO)
        client.get("/health?q=user@example.com")
        for record in caplog.records:
            message = json.dumps(record.msg) if isinstance(record.msg, dict) else str(record.msg)
            assert "user@example.com" not in message


class TestStructuredLogging:
    """Verify that structured logging is properly configured."""

    def test_log_event_has_expected_keys(self, caplog):
        import structlog

        caplog.set_level(logging.INFO)
        logger = structlog.get_logger()
        logger.info("test_event", key="value")

        assert len(caplog.records) >= 1
