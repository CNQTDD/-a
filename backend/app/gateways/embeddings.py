from __future__ import annotations

from app.gateways._base import GatewayPayloadError, HttpGatewayBase


class EmbeddingGateway(HttpGatewayBase):
    async def embed_texts(
        self,
        texts: list[str],
        request_id: str | None = None,
    ) -> list[list[float]]:
        # Embedding 接口只需要文本列表，返回每段文本对应的向量。
        payload = {"model": self._model, "input": texts}
        response = await self._post_json(
            path="/v1/embeddings",
            payload=payload,
            gateway_kind="embedding",
            endpoint_kind="embeddings",
            request_id=request_id,
        )

        data = response.get("data")
        if not isinstance(data, list) or not data:
            raise GatewayPayloadError("embedding response missing data")

        vectors: list[list[float]] = []
        for item in data:
            if not isinstance(item, dict):
                raise GatewayPayloadError("embedding response item must be an object")
            vector = item.get("embedding")
            if not isinstance(vector, list) or not all(
                isinstance(value, (int, float)) for value in vector
            ):
                raise GatewayPayloadError("embedding response missing embedding")
            vectors.append([float(value) for value in vector])
        return vectors
