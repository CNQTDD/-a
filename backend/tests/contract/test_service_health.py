from __future__ import annotations

from pathlib import Path

import yaml


def test_docker_compose_defines_required_services() -> None:
    compose = yaml.safe_load((Path(__file__).parents[3] / "docker-compose.yml").read_text(encoding="utf-8"))

    assert compose["name"] == "suzhida"

    services = compose["services"]
    required = {
        "api",
        "frontend",
        "model-stub",
        "mysql",
        "redis",
        "milvus",
        "etcd",
        "minio",
        "elasticsearch",
        "prometheus",
    }

    assert required.issubset(services.keys())

    api = services["api"]
    assert api["depends_on"]["mysql"]["condition"] == "service_healthy"
    assert api["depends_on"]["redis"]["condition"] == "service_healthy"
    assert api["depends_on"]["milvus"]["condition"] == "service_healthy"
    assert api["depends_on"]["elasticsearch"]["condition"] == "service_healthy"

    assert "volumes" in compose and compose["volumes"]
    assert "networks" in compose and compose["networks"]
    assert compose["networks"]["default"]["internal"] is True
    assert "production" in api["profiles"]
    assert "production" in services["frontend"]["profiles"]
    assert "production" in services["mysql"]["profiles"]
    assert "production" not in services["model-stub"]["profiles"]
    assert services["etcd"]["healthcheck"]["test"] == [
        "CMD",
        "etcdctl",
        "--endpoints=http://127.0.0.1:2379",
        "endpoint",
        "health",
    ]
    assert services["etcd"]["environment"]["ETCDCTL_API"] == "3"
    assert services["milvus"]["environment"]["DEPLOY_MODE"] == "STANDALONE"
    assert services["milvus"]["environment"]["COMMON_STORAGETYPE"] == "local"
