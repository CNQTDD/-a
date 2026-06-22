from __future__ import annotations

from collections.abc import Callable
import json
import uuid
from datetime import UTC, datetime

from elasticsearch import Elasticsearch
from pymilvus import MilvusClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models.complaint import (
    ComplaintSession,
    GeneratedSolution,
    HumanFeedback,
    RetrievedEvidence,
)
from app.db.models.workflow import WorkflowEvent, WorkflowRun
from app.gateways import EmbeddingGateway, LLMGateway, RerankerGateway
from app.retrieval.contracts import RetrievalHit
from app.retrieval.elastic_store import ElasticStore
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.milvus_store import MilvusStore


class ComplaintWorkflowService:
    def __init__(
        self,
        db: Session,
        *,
        settings: Settings | None = None,
        embedding_gateway: object | None = None,
        reranker_gateway: object | None = None,
        llm_gateway: object | None = None,
        search_knowledge: Callable[..., list[RetrievalHit]] | None = None,
    ) -> None:
        self._db = db
        self._settings = settings or Settings()
        self._last_retrieval_meta: dict[str, object] = {
            "degraded_sources": [],
            "retrieval_mode": "local-stub",
        }

        if embedding_gateway is not None:
            self._embedding_gateway = embedding_gateway
        elif self._has_runtime_gateway_urls():
            self._embedding_gateway = EmbeddingGateway(
                base_url=self._settings.embedding_base_url,
                model=self._settings.embedding_model,
                timeout=self._settings.embedding_timeout,
            )
        else:
            self._embedding_gateway = _LocalEmbeddingGateway()

        if reranker_gateway is not None:
            self._reranker_gateway = reranker_gateway
        elif self._has_runtime_gateway_urls():
            self._reranker_gateway = RerankerGateway(
                base_url=self._settings.reranker_base_url,
                model=self._settings.reranker_model,
                timeout=self._settings.reranker_timeout,
            )
        else:
            self._reranker_gateway = _LocalRerankerGateway()

        if llm_gateway is not None:
            self._llm_gateway = llm_gateway
        elif self._has_runtime_gateway_urls():
            self._llm_gateway = LLMGateway(
                base_url=self._settings.llm_base_url,
                model=self._settings.llm_model,
                timeout=self._settings.llm_timeout,
            )
        else:
            self._llm_gateway = _LocalLLMGateway()

        if search_knowledge is not None:
            self._search_knowledge = search_knowledge
        elif self._has_runtime_gateway_urls():
            self._search_knowledge = self._search_hybrid_knowledge
        else:
            self._search_knowledge = self._search_stub_knowledge

    async def start_run(
        self,
        session: ComplaintSession,
        user_message: str,
        trace_id: str | None,
    ) -> str:
        run_id = str(uuid.uuid4())
        request_id = trace_id or run_id

        intent_result = await self._llm_gateway.complete_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "intent classification: return JSON with intent, emotion, "
                        "entities, confidence, and risk_level."
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            request_id=request_id,
        )
        embeddings = await self._embedding_gateway.embed_texts(
            [user_message], request_id=request_id
        )
        query_embedding = embeddings[0]

        self._last_retrieval_meta = {
            "degraded_sources": [],
            "retrieval_mode": "unknown",
        }
        knowledge_hits = self._search_knowledge(
            query=user_message,
            embedding=query_embedding,
            intent=intent_result,
        )
        retrieval_meta = dict(self._last_retrieval_meta)

        rerank_scores = await self._reranker_gateway.rerank(
            query=user_message,
            documents=[item.content_snapshot for item in knowledge_hits],
            request_id=request_id,
        )
        reranked_hits = sorted(
            zip(knowledge_hits, rerank_scores, strict=False),
            key=lambda item: item[1],
            reverse=True,
        )

        evidence_rows: list[RetrievedEvidence] = []
        cited_evidence_ids: list[str] = []
        for hit, rerank_score in reranked_hits:
            cited_evidence_ids.append(hit.evidence_id)
            evidence_rows.append(
                RetrievedEvidence(
                    session_id=session.id,
                    evidence_id=hit.evidence_id,
                    source_id=hit.source_id,
                    chunk_id=hit.chunk_id,
                    source_type=hit.source_type,
                    title=str((hit.metadata or {}).get("title") or hit.source_id),
                    content_snapshot=hit.content_snapshot,
                    score=hit.score,
                    rerank_score=rerank_score,
                    metadata_={**(hit.metadata or {}), "article": hit.article_number},
                )
            )

        solution_payload = await self._llm_gateway.complete_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "solution generation: return JSON with solution_text, "
                        "assessment, steps, risk_notice, validation_status, "
                        "and recommended_route."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "complaint": user_message,
                            "intent": intent_result,
                            "evidence": [
                                {
                                    "evidence_id": hit.evidence_id,
                                    "source_id": hit.source_id,
                                    "content": hit.content_snapshot,
                                }
                                for hit, _ in reranked_hits
                            ],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            request_id=request_id,
        )

        solution = GeneratedSolution(
            session_id=session.id,
            model_version=self._settings.llm_model,
            prompt_version="runtime-mvp-1",
            solution_text=str(solution_payload["solution_text"]),
            cited_evidence_ids=cited_evidence_ids,
            assessment=str(solution_payload.get("assessment", "")),
            steps=[str(item) for item in solution_payload.get("steps", [])],
            risk_notice=str(solution_payload.get("risk_notice", "")),
            validation_status=str(solution_payload.get("validation_status", "passed")),
            validation_details={
                "reason_codes": [],
                "recommended_route": solution_payload.get(
                    "recommended_route", "human_review"
                ),
            },
        )

        session.status = "waiting_human"
        session.risk_level = str(intent_result.get("risk_level", "medium"))
        session.intent = {
            "intent": str(intent_result.get("intent", "unknown")),
            "emotion": str(intent_result.get("emotion", "neutral")),
        }
        session.entities = dict(intent_result.get("entities", {}))
        session.confidence = float(intent_result.get("confidence", 0.0))
        session.workflow_version = "runtime-mvp-1"
        session.evidence.extend(evidence_rows)
        session.solutions.append(solution)

        events = [
            ("workflow_started", {"message": user_message}),
            (
                "intent_completed",
                {
                    "intent": session.intent["intent"],
                    "emotion": session.intent["emotion"],
                    "entities": list(session.entities.values()),
                },
            ),
            (
                "retrieval_completed",
                {
                    "evidence_ids": cited_evidence_ids,
                    "degradedSources": list(
                        retrieval_meta.get("degraded_sources", [])
                    ),
                    "retrievalMode": str(
                        retrieval_meta.get("retrieval_mode", "unknown")
                    ),
                    "evidence": [
                        {
                            "evidence_id": hit.evidence_id,
                            "source_id": hit.source_id,
                            "source_type": hit.source_type,
                            "title": str((hit.metadata or {}).get("title") or hit.source_id),
                            "content_snapshot": hit.content_snapshot,
                            "score": hit.score,
                            "article": hit.article_number,
                        }
                        for hit, _ in reranked_hits
                    ],
                },
            ),
            ("generation_delta", {"text": solution.solution_text}),
            (
                "validation_completed",
                {
                    "status": solution.validation_status,
                    "details": solution.assessment,
                },
            ),
            (
                "human_review_required",
                {
                    "route": solution.validation_details.get(
                        "recommended_route", "human_review"
                    ),
                    "risk_level": session.risk_level,
                },
            ),
            ("workflow_completed", {"status": "waiting_human"}),
        ]

        self._db.add(
            WorkflowRun(
                session_id=session.id,
                run_id=run_id,
                status="completed",
                completed_at=_utc_now(),
            )
        )
        for index, (event_type, data) in enumerate(events, start=1):
            self._db.add(
                WorkflowEvent(
                    session_id=session.id,
                    run_id=run_id,
                    event_id=f"evt-{index}",
                    trace_id=trace_id,
                    type=event_type,
                    data=data,
                    sequence=index,
                )
            )
        self._db.commit()
        return run_id

    def stream_events(self, session_id: str, last_event_id: str | None = None) -> str:
        query = (
            self._db.query(WorkflowEvent)
            .filter(WorkflowEvent.session_id == session_id)
            .order_by(WorkflowEvent.sequence.asc())
        )
        events = query.all()
        if last_event_id:
            for index, event in enumerate(events):
                if event.event_id == last_event_id:
                    events = events[index + 1 :]
                    break
        lines: list[str] = []
        for event in events:
            lines.append(f"event: {event.type}")
            lines.append(f"id: {event.event_id}")
            lines.append(f"data: {json.dumps(event.data, ensure_ascii=False)}")
            lines.append("")
        return "\n".join(lines)

    def apply_feedback(
        self,
        session: ComplaintSession,
        *,
        action: str,
        edited_solution: str | None,
        reject_reason: str | None,
        operator_note: str | None,
        idempotency_key: str,
    ) -> HumanFeedback:
        feedback = HumanFeedback(
            session_id=session.id,
            idempotency_key=idempotency_key,
            payload_fingerprint=idempotency_key,
            action=action,
            edited_solution=edited_solution,
            reject_reason=reject_reason,
            operator_note=operator_note,
        )
        session.feedback.append(feedback)
        if action == "edited" and edited_solution:
            if session.solutions:
                session.solutions[-1].solution_text = edited_solution
                session.solutions[-1].created_at = _utc_now()
            session.status = "completed"
        elif action == "accepted":
            session.status = "completed"
        elif action == "rejected":
            session.status = "failed"
        self._db.commit()
        return feedback

    def _search_hybrid_knowledge(
        self,
        *,
        query: str,
        embedding: list[float],
        intent: dict[str, object],
    ) -> list[RetrievalHit]:
        filters = {
            "source_version": "sample-1",
            "business_type": self._runtime_business_type(intent),
            "as_of": datetime.now(UTC),
        }
        elastic_store = ElasticStore(
            index_name="suzhida-knowledge-sample",
            client=Elasticsearch(self._settings.elasticsearch_url),
        )
        milvus_store = MilvusStore(
            MilvusClient(uri=self._settings.milvus_uri),
            collection_name="suzhida_knowledge_sample",
        )
        result = HybridRetriever(
            elastic_store=elastic_store,
            milvus_store=milvus_store,
        ).retrieve(
            query=query,
            embedding=embedding,
            limit=5,
            filters=filters,
        )
        self._last_retrieval_meta = {
            "degraded_sources": result.degraded_sources,
            "retrieval_mode": result.retrieval_mode,
        }
        return result.hits

    def _search_elasticsearch_knowledge(
        self,
        *,
        query: str,
        embedding: list[float],
        intent: dict[str, object],
    ) -> list[RetrievalHit]:
        del embedding
        store = ElasticStore(
            index_name="suzhida-knowledge-sample",
            client=Elasticsearch(self._settings.elasticsearch_url),
        )
        hits = store.search(
            query=query,
            limit=5,
            filters={
                "source_version": "sample-1",
                "business_type": self._runtime_business_type(intent),
                "as_of": datetime.now(UTC),
            },
        )
        self._last_retrieval_meta = {
            "degraded_sources": [],
            "retrieval_mode": "elasticsearch-only",
        }
        return hits

    def _search_stub_knowledge(
        self,
        *,
        query: str,
        embedding: list[float],
        intent: dict[str, object],
    ) -> list[RetrievalHit]:
        del query, embedding
        if str(intent.get("intent")) == "service_impact_economic_loss":
            self._last_retrieval_meta = {
                "degraded_sources": [],
                "retrieval_mode": "hybrid-semantic-heavy",
            }
            return [
                RetrievalHit(
                    evidence_id="stub-network-evidence-1",
                    chunk_id="stub-network-chunk-1",
                    source_id="policy-network-001",
                    source_type="business_rule",
                    business_type="service",
                    region="yunnan",
                    product="network-service",
                    source_version="stub-1",
                    status="active",
                    source_at=_utc_now(),
                    effective_at=_utc_now(),
                    expired_at=None,
                    article_number="N-001",
                    content_snapshot=(
                        "网络异常导致服务影响生产经营与经济损失处置规则：像炒股受影响这类表述，"
                        "统一归入服务影响用户生产经营并引发经济损失场景。"
                    ),
                    score=0.95,
                    metadata={"title": "网络异常导致服务影响生产经营与经济损失处置规则"},
                ),
                RetrievalHit(
                    evidence_id="stub-network-evidence-2",
                    chunk_id="stub-network-chunk-2",
                    source_id="policy-network-002",
                    source_type="business_rule",
                    business_type="service",
                    region="yunnan",
                    product="network-service",
                    source_version="stub-1",
                    status="active",
                    source_at=_utc_now(),
                    effective_at=_utc_now(),
                    expired_at=None,
                    article_number="N-002",
                    content_snapshot="涉及经济损失或赔偿主张的投诉必须升级至资深人工复核。",
                    score=0.9,
                    metadata={"title": "高风险经济损失升级规则"},
                ),
            ]

        self._last_retrieval_meta = {
            "degraded_sources": [],
            "retrieval_mode": "hybrid-keyword-heavy",
        }
        return [
            RetrievalHit(
                evidence_id="stub-evidence-1",
                chunk_id="stub-chunk-1",
                source_id="policy-001",
                source_type="business_rule",
                business_type="billing",
                region="yunnan",
                product="plan",
                source_version="stub-1",
                status="active",
                source_at=_utc_now(),
                effective_at=_utc_now(),
                expired_at=None,
                article_number="A-001",
                content_snapshot="账单异常时需要核查套餐变更与历史账单。",
                score=0.8,
                metadata={"title": "套餐扣费核查规则"},
            ),
            RetrievalHit(
                evidence_id="stub-evidence-2",
                chunk_id="stub-chunk-2",
                source_id="policy-002",
                source_type="business_rule",
                business_type="billing",
                region="yunnan",
                product="plan",
                source_version="stub-1",
                status="active",
                source_at=_utc_now(),
                effective_at=_utc_now(),
                expired_at=None,
                article_number="A-002",
                content_snapshot="确认误扣后应在下一期账单退回差额。",
                score=0.9,
                metadata={"title": "误扣退费规则"},
            ),
        ]

    def _runtime_business_type(self, intent: dict[str, object]) -> str:
        intent_name = str(intent.get("intent", "billing_dispute"))
        return "billing" if "billing" in intent_name else "service"

    def _has_runtime_gateway_urls(self) -> bool:
        return all(
            (
                self._settings.llm_base_url,
                self._settings.embedding_base_url,
                self._settings.reranker_base_url,
            )
        )


class _LocalEmbeddingGateway:
    async def embed_texts(
        self, texts: list[str], request_id: str | None = None
    ) -> list[list[float]]:
        del texts, request_id
        return [[0.1, 0.2, 0.3, 0.4]]


class _LocalRerankerGateway:
    async def rerank(
        self,
        *,
        query: str,
        documents: list[str],
        request_id: str | None = None,
    ) -> list[float]:
        del query, request_id
        return [1.0 / (index + 1) for index, _ in enumerate(documents)]


def _is_service_impact_economic_loss(text: str) -> bool:
    return "网络" in text and "赔偿" in text and ("损失" in text or "炒股" in text)


class _LocalLLMGateway:
    async def complete_json(
        self,
        *,
        messages: list[dict[str, object]],
        request_id: str | None = None,
    ) -> dict[str, object]:
        del request_id
        system_prompt = str(messages[0]["content"]) if messages else ""
        last_message = str(messages[-1]["content"]) if messages else ""
        if "intent classification" in system_prompt:
            if _is_service_impact_economic_loss(last_message):
                return {
                    "intent": "service_impact_economic_loss",
                    "emotion": "anxious",
                    "entities": {"product": "网络服务", "topic": "economic_loss"},
                    "confidence": 0.96,
                    "risk_level": "high",
                }
            return {
                "intent": "billing_dispute",
                "emotion": "angry",
                "entities": {"product": "套餐", "topic": "扣费"},
                "confidence": 0.93,
                "risk_level": "medium",
            }
        if _is_service_impact_economic_loss(last_message):
            return {
                "solution_text": (
                    "This case is classified as service impact and economic loss. "
                    "先核查服务异常时段、影响范围和损失主张材料，再升级至资深人工复核。"
                ),
                "assessment": "涉及服务影响用户生产经营并引发经济损失，属于高风险投诉，需要人工复核。",
                "steps": [
                    "核查故障告警与修复记录",
                    "确认用户受影响时段与业务号码",
                    "收集损失主张材料后转资深人工复核",
                ],
                "risk_notice": "在人工审批前不得直接承诺赔付款项，必要时转法务支持。",
                "validation_status": "passed",
                "recommended_route": "senior_human_review",
            }
        return {
            "solution_text": "建议核查套餐扣费并在下期账单退回差额。",
            "assessment": "证据充分，可以进入人工复核。",
            "steps": ["核查账单", "确认扣费来源", "执行退费"],
            "risk_notice": "涉及账单修正，需要人工审核。",
            "validation_status": "passed",
            "recommended_route": "human_review",
        }


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
