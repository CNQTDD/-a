import pytest
from pydantic import ValidationError

from app.domain.schemas import FeedbackCreate


def test_rejected_feedback_requires_reason() -> None:
    with pytest.raises(ValidationError):
        FeedbackCreate(action="rejected")


def test_edited_feedback_requires_solution() -> None:
    with pytest.raises(ValidationError):
        FeedbackCreate(action="edited")


def test_accepted_feedback_is_valid() -> None:
    fb = FeedbackCreate(action="accepted")
    assert fb.action == "accepted"
    assert fb.reject_reason is None
    assert fb.edited_solution is None


def test_schema_factory() -> None:
    fb = FeedbackCreate(action="rejected", reject_reason="Not applicable")
    assert fb.action == "rejected"
    assert fb.reject_reason == "Not applicable"
