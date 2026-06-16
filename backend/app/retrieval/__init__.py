"""检索层适配器入口。"""

from app.retrieval.contracts import RetrievalHit, VectorRecord
from app.retrieval.milvus_store import MilvusStore

__all__ = ["MilvusStore", "RetrievalHit", "VectorRecord"]
