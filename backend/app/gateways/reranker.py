from __future__ import annotations

from app.gateways._base import GatewayPayloadError, HttpGatewayBase


class RerankerGateway(HttpGatewayBase):
    async def rerank(
        self,
        *,
        query: str,
        documents: list[str],
        request_id: str | None = None,
    ) -> list[float]:
        # Reranker 接口同时接收查询和候选文档，返回每个候选文档的分值。
        payload = {"model": self._model, "query": query, "documents": documents}
        response = await self._post_json(
            path="/v1/rerank",
            payload=payload,
            gateway_kind="reranker",
            endpoint_kind="rerank",
            request_id=request_id,
        )

        if "scores" in response:
            scores = response["scores"]
            if not isinstance(scores, list):
                raise GatewayPayloadError("reranker scores must be a list")
            if not all(isinstance(score, (int, float)) for score in scores):
                raise GatewayPayloadError("reranker scores must be numeric")
            return [float(score) for score in scores]

        results = response.get("results")
        if results is None:
            raise GatewayPayloadError("reranker response missing scores")
        if not isinstance(results, list):
            raise GatewayPayloadError("reranker response results must be a list")

        scores: list[float] = []
        for item in results:
            if not isinstance(item, dict) or "score" not in item:
                raise GatewayPayloadError("reranker response result missing score")
            score = item["score"]
            if not isinstance(score, (int, float)):
                raise GatewayPayloadError("reranker score must be numeric")
            scores.append(float(score))
        return scores
