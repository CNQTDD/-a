from __future__ import annotations


class DomainError(Exception):
    """Base for domain-layer errors."""

    pass


class EntityNotFoundError(DomainError):
    def __init__(self, entity: str, identifier: str) -> None:
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity} not found: {identifier}")


class CitationOwnershipError(DomainError):
    def __init__(self, evidence_id: str, session_id: str) -> None:
        self.evidence_id = evidence_id
        self.session_id = session_id
        super().__init__(
            f"Evidence {evidence_id} does not belong to session {session_id}"
        )


class FeedbackAlreadyExistsError(DomainError):
    def __init__(self, session_id: str, idempotency_key: str) -> None:
        self.session_id = session_id
        self.idempotency_key = idempotency_key
        message = (
            f"Feedback already exists for session {session_id} "
            f"with key {idempotency_key}"
        )
        super().__init__(message)


class SessionNotRunnableError(DomainError):
    def __init__(self, session_id: str, status: str) -> None:
        self.session_id = session_id
        self.status = status
        super().__init__(f"Session {session_id} is in status {status} and cannot run")


__all__ = [
    "DomainError",
    "EntityNotFoundError",
    "CitationOwnershipError",
    "FeedbackAlreadyExistsError",
    "SessionNotRunnableError",
]
