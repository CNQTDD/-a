from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class APIError(Exception):
    status_code: int
    code: str
    message: str


class NotFoundError(APIError):
    def __init__(self, entity: str, identifier: Any) -> None:
        super().__init__(
            status_code=404,
            code="NOT_FOUND",
            message=f"{entity} not found: {identifier}",
        )


class ConflictError(APIError):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=409,
            code="CONFLICT",
            message=message,
        )


class ValidationError(APIError):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=422,
            code="VALIDATION_ERROR",
            message=message,
        )
