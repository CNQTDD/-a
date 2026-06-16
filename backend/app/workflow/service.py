from __future__ import annotations

import json
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.complaint import ComplaintSession, GeneratedSolution, HumanFeedback, RetrievedEvidence
from app.db.models.workflow import WorkflowEvent, WorkflowRun


class ComplaintWorkflowService:
    def __init__(self, db: Session):
        self._db = db

    def start_run(self, session: ComplaintSession, user_message: str, trace_id: str | None) -> str:
        run_id = str(uuid.uuid4())
        evidence_id = f"ev-{uuid.uuid4().hex[:8]}"

        evidence = RetrievedEvidence(
            session_id=session.id,
            evidence_id=evidence_id,
            source_id="policy-001",
            chunk_id="policy-001-1",
            source_type="business_rule",
            title="套餐扣费核查规则",
            content_snapshot="账单异常时，客服需先核查套餐变更与历史账单。",
            score=0.99,
            rerank_score=0.98,
            metadata_={"article": "A-001"},
        )
        solution = GeneratedSolution(
            session_id=session.id,
            model_version="Qwen2.5-14B-Instruct",
            prompt_version="mvp-1",
            solution_text="建议核查账单并在下期账单中退回差额。",
            cited_evidence_ids=[evidence_id],
            assessment="引用完整，需人工确认后处理。",
            steps=["核查账单", "确认扣费来源", "执行退回"],
            risk_notice="涉及账单修正，需人工审核。",
            validation_status="passed",
            validation_details={"reason_codes": [], "recommended_route": "human_review"},
        )
        session.status = "waiting_human"
        session.risk_level = "medium"
        session.intent = {"intent": "billing_dispute", "summary": user_message}
        session.entities = {"product": "套餐", "topic": "扣费"}
        session.confidence = 0.98
        session.workflow_version = "mvp-1"
        session.evidence.append(evidence)
        session.solutions.append(solution)

        events = [
            ("workflow_started", {"message": user_message}),
            ("intent_completed", {"intent": "billing_dispute"}),
            ("retrieval_completed", {"evidence_ids": [evidence_id]}),
            ("generation_delta", {"text": solution.solution_text}),
            ("validation_completed", {"status": "passed"}),
            ("human_review_required", {"route": "human_review"}),
            ("workflow_completed", {"status": "waiting_human"}),
        ]
        self._db.add(WorkflowRun(session_id=session.id, run_id=run_id, status="completed"))
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
        lines = []
        for event in events:
            lines.append(f"event: {event.type}")
            lines.append(f"id: {event.event_id}")
            lines.append(f"data: {json.dumps(event.data, ensure_ascii=False)}")
            lines.append("")
        return "\n".join(lines)

    def apply_feedback(self, session: ComplaintSession, *, action: str, edited_solution: str | None, reject_reason: str | None, operator_note: str | None, idempotency_key: str) -> HumanFeedback:
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
                session.solutions[-1].created_at = datetime.utcnow()
            session.status = "completed"
        elif action == "accepted":
            session.status = "completed"
        elif action == "rejected":
            session.status = "failed"
        self._db.commit()
        return feedback
