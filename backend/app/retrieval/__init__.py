"""检索层适配器入口。"""

from app.retrieval.contracts import RetrievalHit, TemplateRecord, VectorRecord
from app.retrieval.elastic_store import ElasticStore
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.milvus_store import MilvusStore
from app.retrieval.template_store import TemplateStore

__all__ = [
    "ElasticStore",
    "HybridRetriever",
    "MilvusStore",
    "RetrievalHit",
    "TemplateRecord",
    "TemplateStore",
    "VectorRecord",
]
