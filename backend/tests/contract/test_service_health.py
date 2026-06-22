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
    assert api["ports"] == ["127.0.0.1:8000:8000"]
    assert services["frontend"]["ports"] == ["127.0.0.1:5280:4173"]

    assert "volumes" in compose and compose["volumes"]
    assert "networks" in compose and compose["networks"]
    assert compose["networks"]["default"]["name"] == "suzhida-internal"
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


def test_frontend_dockerfile_uses_pinned_base_image() -> None:
    dockerfile = (Path(__file__).parents[3] / "frontend" / "Dockerfile").read_text(encoding="utf-8")

    first_line = dockerfile.splitlines()[0]

    assert ":latest" not in first_line
    assert first_line.startswith("FROM ")
    assert ":" in first_line


def test_stack_verification_runs_full_frontend_e2e_suite() -> None:
    script = (Path(__file__).parents[3] / "scripts" / "verify-stack.ps1").read_text(encoding="utf-8")

    assert "node_modules\\playwright\\cli.js test --config $playwrightConfig" in script
    assert "./tests/e2e/degraded-flow.spec.ts" not in script


def test_post_deploy_checks_and_operations_runbook_exist() -> None:
    root = Path(__file__).parents[3]
    script = (root / "scripts" / "post-deploy-check.ps1").read_text(encoding="utf-8")
    runbook = (root / "docs" / "deployment" / "operations-runbook.md").read_text(encoding="utf-8")

    assert "Invoke-RestMethod" in script
    assert "/health" in script
    assert "/metrics" in script
    assert "http://127.0.0.1:5280" in script
    assert "异常处置" in runbook
    assert "回滚" in runbook
