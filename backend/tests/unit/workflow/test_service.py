from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.db.models.complaint import ComplaintSession, User
from app.domain.schemas import SessionCreate
from app.retrieval.contracts import RetrievalHit
from app.workflow.service import ComplaintWorkflowService


USER_ID = "workflow-user"


@dataclass
class FakeEmbeddingGateway:
    calls: list[tuple[list[str], str | None]]

    async def embed_texts(
        self, texts: list[str], request_id: str | None = None
    ) -> list[list[float]]:
        self.calls.append((texts, request_id))
        return [[0.11, 0.22, 0.33]]


@dataclass
class FakeRerankerGateway:
    calls: list[tuple[str, list[str], str | None]]

    async def rerank(
        self,
        *,
        query: str,
        documents: list[str],
        request_id: str | None = None,
    ) -> list[float]:
        self.calls.append((query, documents, request_id))
        return [0.2, 0.9]


@dataclass
class FakeLLMGateway:
    calls: list[tuple[list[dict[str, object]], str | None]]

    async def complete_json(
        self,
        *,
        messages: list[dict[str, object]],
        request_id: str | None = None,
    ) -> dict[str, object]:
        self.calls.append((messages, request_id))
        system_prompt = str(messages[0]["content"])
        if "intent classification" in system_prompt:
            return {
                "intent": "billing_dispute",
                "emotion": "angry",
                "entities": {"product": "plan", "topic": "billing"},
                "confidence": 0.93,
                "risk_level": "medium",
            }
        return {
            "solution_text": (
                "Review the billing records and refund the overcharge on the next "
                "statement."
            ),
            "assessment": "The evidence is sufficient for human review.",
            "steps": [
                "Review the monthly statement",
                "Confirm the overcharge source",
                "Issue the refund adjustment",
            ],
            "risk_notice": "Billing corrections require human approval.",
            "validation_status": "passed",
            "recommended_route": "human_review",
        }


def _hits() -> list[RetrievalHit]:
    return [
        RetrievalHit(
            evidence_id="evidence-1",
            chunk_id="chunk-1",
            source_id="rule-1",
            source_type="business_rule",
            business_type="billing",
            region="yunnan",
            product="5g-plan",
            source_version="sample-1",
            status="active",
            source_at=datetime(2026, 1, 1),
            effective_at=datetime(2026, 1, 1),
            expired_at=None,
            article_number="A-001",
            content_snapshot="Rule one: verify whether the plan changed on the bill.",
            score=0.4,
            metadata={"title": "Billing review rule"},
        ),
        RetrievalHit(
            evidence_id="evidence-2",
            chunk_id="chunk-2",
            source_id="rule-2",
            source_type="business_rule",
            business_type="billing",
            region="yunnan",
            product="5g-plan",
            source_version="sample-1",
            status="active",
            source_at=datetime(2026, 1, 1),
            effective_at=datetime(2026, 1, 1),
            expired_at=None,
            article_number="A-002",
            content_snapshot=(
                "Rule two: once the overcharge is confirmed, refund it in the next "
                "statement."
            ),
            score=0.7,
            metadata={"title": "Overcharge refund rule"},
        ),
    ]


def _create_session(db_session: Session) -> ComplaintSession:
    db_session.add(User(id=USER_ID, name="Workflow Tester", role="agent"))
    db_session.commit()

    from app.db.repositories.complaints import ComplaintRepository

    payload = SessionCreate(
        user_id=USER_ID,
        complaint_text="The plan billing appears incorrect and needs review.",
        client_request_id="workflow-test-1",
    )
    session, created = ComplaintRepository(db_session).create_or_get(payload)
    assert created is True
    return session


@pytest.mark.asyncio
async def test_start_run_uses_gateways_and_retrieval_results(db_session: Session) -> None:
    session = _create_session(db_session)
    embedding_gateway = FakeEmbeddingGateway(calls=[])
    reranker_gateway = FakeRerankerGateway(calls=[])
    llm_gateway = FakeLLMGateway(calls=[])
    retrieval_calls: list[tuple[str, list[float], dict[str, object]]] = []

    def search_knowledge(
        *, query: str, embedding: list[float], intent: dict[str, object]
    ) -> list[RetrievalHit]:
        retrieval_calls.append((query, embedding, intent))
        return _hits()

    service = ComplaintWorkflowService(
        db_session,
        embedding_gateway=embedding_gateway,
        reranker_gateway=reranker_gateway,
        llm_gateway=llm_gateway,
        search_knowledge=search_knowledge,
    )

    run_id = await service.start_run(
        session,
        "Please check last month's plan charge.",
        "trace-workflow-1",
    )

    assert run_id
    assert embedding_gateway.calls == [
        (["Please check last month's plan charge."], "trace-workflow-1")
    ]
    assert len(llm_gateway.calls) == 2
    assert retrieval_calls[0][0] == "Please check last month's plan charge."
    assert retrieval_calls[0][1] == [0.11, 0.22, 0.33]
    assert reranker_gateway.calls[0][1] == [
        "Rule one: verify whether the plan changed on the bill.",
        "Rule two: once the overcharge is confirmed, refund it in the next statement.",
    ]

    db_session.refresh(session)
    assert session.status == "waiting_human"
    assert session.intent == {"intent": "billing_dispute", "emotion": "angry"}
    assert session.entities == {"product": "plan", "topic": "billing"}
    assert [item.source_id for item in session.evidence] == ["rule-2", "rule-1"]
    assert session.solutions[-1].cited_evidence_ids == ["evidence-2", "evidence-1"]


@pytest.mark.asyncio
async def test_start_run_local_fallback_generates_readable_solution_text(
    db_session: Session,
) -> None:
    session = _create_session(db_session)
    service = ComplaintWorkflowService(db_session)

    await service.start_run(
        session,
        "Please review the double-billing complaint and propose a next step.",
        "trace-workflow-local-fallback",
    )

    db_session.refresh(session)
    assert session.status == "waiting_human"
    assert session.solutions[-1].solution_text.startswith("建议核查套餐扣费")
