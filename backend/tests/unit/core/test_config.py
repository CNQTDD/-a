from app.core.config import Settings


def test_settings_never_expose_raw_complaint_logging() -> None:
    assert not hasattr(Settings(), "log_raw_complaints")


def test_settings_use_versioned_api_prefix() -> None:
    assert Settings().api_prefix == "/api/v1"
