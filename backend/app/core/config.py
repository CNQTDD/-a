from __future__ import annotations

import enum
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, enum.Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    environment: Environment = Environment.DEVELOPMENT
    service_name: str = "suzhida-api"
    api_prefix: str = "/api/v1"

    # Database
    database_url: str = "sqlite+pysqlite:///./.tmp/suzhida.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Milvus
    milvus_uri: str = "http://localhost:19530"

    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9200"

    # Model gateways
    llm_base_url: str = ""
    llm_model: str = "Qwen2.5-14B-Instruct"
    embedding_base_url: str = ""
    embedding_model: str = "BAAI/bge-m3"
    reranker_base_url: str = ""
    reranker_model: str = "BAAI/bge-reranker-v2-m3"

    # Timeouts (seconds)
    llm_timeout: float = 60.0
    embedding_timeout: float = 30.0
    reranker_timeout: float = 30.0

    # Workflow
    workflow_max_retries: int = 2

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("environment", mode="after")
    @classmethod
    def production_requires_real_gateways(cls, v: Environment, info) -> Environment:
        if v == Environment.PRODUCTION:
            for key in ("llm_base_url", "embedding_base_url", "reranker_base_url"):
                url = info.data.get(key, "")
                if not url or url.startswith("fake://"):
                    raise ValueError(
                        f"Production environment requires a real {key}."
                        f" Got: {url!r}"
                    )
        return v
