from __future__ import annotations

import enum


class SessionStatus(str, enum.Enum):
    CREATED = "created"
    RUNNING = "running"
    WAITING_HUMAN = "waiting_human"
    COMPLETED = "completed"
    FAILED = "failed"


class FeedbackAction(str, enum.Enum):
    ACCEPTED = "accepted"
    EDITED = "edited"
    REJECTED = "rejected"


class SourceType(str, enum.Enum):
    HISTORICAL_TICKET = "historical_ticket"
    BUSINESS_RULE = "business_rule"
    TEMPLATE = "template"


class ValidationStatus(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UserRole(str, enum.Enum):
    AGENT = "agent"
    SUPERVISOR = "supervisor"
    KNOWLEDGE_ADMIN = "knowledge_admin"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class KnowledgeStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    STAGED = "staged"
    ACTIVE = "active"
    EXPIRED = "expired"
    FAILED = "failed"
