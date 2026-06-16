from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GatewayError(RuntimeError):
    """网关层统一错误基类。"""


class GatewayTimeoutError(GatewayError):
    """请求超时或重试后仍然超时。"""


class GatewayResponseError(GatewayError):
    """上游返回 4xx / 5xx 时抛出。"""

    def __init__(self, gateway_kind: str, status_code: int) -> None:
        super().__init__(f"{gateway_kind} gateway returned HTTP {status_code}")
        self.gateway_kind = gateway_kind
        self.status_code = status_code


class GatewayPayloadError(GatewayError):
    """上游返回结构不符合契约时抛出。"""


@dataclass(frozen=True)
class GatewayAuditRecord:
    """审计日志只保留元数据，不携带原始敏感文本。"""

    gateway_kind: str
    endpoint_kind: str
    request_id: str
    model: str
    status: str
    latency_ms: int
    usage: dict[str, int] | None = None
    item_count: int | None = None


class HttpGatewayBase:
    """所有模型网关的公共请求骨架。"""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        transport: httpx.MockTransport | None = None,
        timeout: float = 30.0,
        max_retries: int = 0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._transport = transport
        self._timeout = timeout
        self._max_retries = max_retries

    def _request_id(self, request_id: str | None) -> str:
        return request_id or str(uuid.uuid4())

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            transport=self._transport,
        )

    def _log_audit(self, record: GatewayAuditRecord) -> None:
        # 只写入元数据，避免把原始投诉文本、身份证号、手机号带进日志。
        logger.info("gateway_audit %s", asdict(record))

    def _log_failure(self, record: GatewayAuditRecord) -> None:
        # 失败也只记录元数据，方便后续排障和统计。
        logger.warning("gateway_audit %s", asdict(record))

    async def _post_json(
        self,
        *,
        path: str,
        payload: dict[str, Any],
        gateway_kind: str,
        endpoint_kind: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        rid = self._request_id(request_id)
        attempts = 0
        while True:
            started_at = time.perf_counter()
            try:
                async with self._client() as client:
                    response = await client.post(path, json=payload)
            except httpx.TimeoutException as exc:
                latency_ms = int((time.perf_counter() - started_at) * 1000)
                failure = GatewayAuditRecord(
                    gateway_kind=gateway_kind,
                    endpoint_kind=endpoint_kind,
                    request_id=rid,
                    model=self._model,
                    status="timeout",
                    latency_ms=latency_ms,
                )
                if attempts < self._max_retries:
                    attempts += 1
                    continue
                self._log_failure(failure)
                raise GatewayTimeoutError(f"{gateway_kind} request timed out") from exc

            latency_ms = int((time.perf_counter() - started_at) * 1000)
            if 500 <= response.status_code < 600:
                failure = GatewayAuditRecord(
                    gateway_kind=gateway_kind,
                    endpoint_kind=endpoint_kind,
                    request_id=rid,
                    model=self._model,
                    status="retryable_error",
                    latency_ms=latency_ms,
                )
                if attempts < self._max_retries:
                    attempts += 1
                    continue
                self._log_failure(failure)
                raise GatewayResponseError(gateway_kind, response.status_code)

            if response.status_code >= 400:
                failure = GatewayAuditRecord(
                    gateway_kind=gateway_kind,
                    endpoint_kind=endpoint_kind,
                    request_id=rid,
                    model=self._model,
                    status="client_error",
                    latency_ms=latency_ms,
                )
                self._log_failure(failure)
                raise GatewayResponseError(gateway_kind, response.status_code)

            payload_json = response.json()
            self._log_audit(
                GatewayAuditRecord(
                    gateway_kind=gateway_kind,
                    endpoint_kind=endpoint_kind,
                    request_id=rid,
                    model=self._model,
                    status="ok",
                    latency_ms=latency_ms,
                )
            )
            return payload_json

    async def _stream_lines(
        self,
        *,
        path: str,
        payload: dict[str, Any],
        gateway_kind: str,
        endpoint_kind: str,
        request_id: str | None,
    ):
        rid = self._request_id(request_id)
        attempts = 0
        while True:
            started_at = time.perf_counter()
            try:
                async with self._client() as client:
                    async with client.stream("POST", path, json=payload) as response:
                        latency_ms = int((time.perf_counter() - started_at) * 1000)
                        if 500 <= response.status_code < 600:
                            if attempts < self._max_retries:
                                attempts += 1
                                continue
                            self._log_failure(
                                GatewayAuditRecord(
                                    gateway_kind=gateway_kind,
                                    endpoint_kind=endpoint_kind,
                                    request_id=rid,
                                    model=self._model,
                                    status="retryable_error",
                                    latency_ms=latency_ms,
                                )
                            )
                            raise GatewayResponseError(
                                gateway_kind,
                                response.status_code,
                            )
                        if response.status_code >= 400:
                            self._log_failure(
                                GatewayAuditRecord(
                                    gateway_kind=gateway_kind,
                                    endpoint_kind=endpoint_kind,
                                    request_id=rid,
                                    model=self._model,
                                    status="client_error",
                                    latency_ms=latency_ms,
                                )
                            )
                            raise GatewayResponseError(
                                gateway_kind,
                                response.status_code,
                            )

                        async for line in response.aiter_lines():
                            if not line or not line.startswith("data:"):
                                continue
                            data = line.removeprefix("data:").strip()
                            if data == "[DONE]":
                                self._log_audit(
                                    GatewayAuditRecord(
                                        gateway_kind=gateway_kind,
                                        endpoint_kind=endpoint_kind,
                                        request_id=rid,
                                        model=self._model,
                                        status="ok",
                                        latency_ms=latency_ms,
                                    )
                                )
                                return
                            yield data

                        self._log_audit(
                            GatewayAuditRecord(
                                gateway_kind=gateway_kind,
                                endpoint_kind=endpoint_kind,
                                request_id=rid,
                                model=self._model,
                                status="ok",
                                latency_ms=latency_ms,
                            )
                        )
                        return
            except httpx.TimeoutException as exc:
                latency_ms = int((time.perf_counter() - started_at) * 1000)
                failure = GatewayAuditRecord(
                    gateway_kind=gateway_kind,
                    endpoint_kind=endpoint_kind,
                    request_id=rid,
                    model=self._model,
                    status="timeout",
                    latency_ms=latency_ms,
                )
                if attempts < self._max_retries:
                    attempts += 1
                    continue
                self._log_failure(failure)
                raise GatewayTimeoutError(f"{gateway_kind} request timed out") from exc


def parse_json_payload(payload: str | dict[str, Any]) -> dict[str, Any]:
    """把 OpenAI 风格的字符串内容转换为 JSON 对象。"""
    if isinstance(payload, dict):
        return payload
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise GatewayPayloadError("invalid JSON payload") from exc
    if not isinstance(parsed, dict):
        raise GatewayPayloadError("JSON payload must be an object")
    return parsed
