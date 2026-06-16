from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_requires_private_model_gateways() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production")


@pytest.mark.parametrize(
    ("llm_base_url", "embedding_base_url", "reranker_base_url"),
    [
        ("fake://llm", "http://embedding", "http://reranker"),
        ("http://llm", "fake://embedding", "http://reranker"),
        ("http://llm", "http://embedding", "fake://reranker"),
    ],
)
def test_fake_gateway_schemes_are_rejected_in_production(
    llm_base_url: str,
    embedding_base_url: str,
    reranker_base_url: str,
) -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            llm_base_url=llm_base_url,
            embedding_base_url=embedding_base_url,
            reranker_base_url=reranker_base_url,
        )
