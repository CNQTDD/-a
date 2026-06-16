from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from app.gateways._base import GatewayPayloadError, HttpGatewayBase, parse_json_payload


class LLMGateway(HttpGatewayBase):
    async def complete_json(
        self,
        *,
        messages: list[dict[str, Any]],
        request_id: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "model": self._model,
            "messages": messages,
            "response_format": {"type": "json_object"},
        }
        response = await self._post_json(
            path="/v1/chat/completions",
            payload=payload,
            gateway_kind="llm",
            endpoint_kind="chat_completions",
            request_id=request_id,
        )

        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise GatewayPayloadError("LLM response missing choices")
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise GatewayPayloadError("LLM response choice must be an object")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise GatewayPayloadError("LLM response missing message")
        content = message.get("content")
        if content is None:
            raise GatewayPayloadError("LLM response missing content")
        return parse_json_payload(content)

    async def stream_completion(
        self,
        *,
        messages: list[dict[str, Any]],
        request_id: str | None = None,
    ) -> AsyncIterator[str]:
        payload = {"model": self._model, "messages": messages, "stream": True}
        async for line in self._stream_lines(
            path="/v1/chat/completions",
            payload=payload,
            gateway_kind="llm",
            endpoint_kind="chat_stream",
            request_id=request_id,
        ):
            event = parse_json_payload(line)
            choices = event.get("choices")
            if not isinstance(choices, list) or not choices:
                raise GatewayPayloadError("stream chunk missing choices")
            first_choice = choices[0]
            if not isinstance(first_choice, dict):
                raise GatewayPayloadError("stream chunk choice must be an object")
            delta = first_choice.get("delta")
            if not isinstance(delta, dict):
                raise GatewayPayloadError("stream chunk missing delta")
            content = delta.get("content")
            if isinstance(content, str) and content:
                yield content
