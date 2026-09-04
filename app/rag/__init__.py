from langchain_community.embeddings import DashScopeEmbeddings
from langchain_milvus import BM25BuiltInFunction, Milvus

from app.core.config import settings
from app.rag.pipeline import RAGPipeline
from app.rag.retriever import ParentChunkRetriever

# 1.初始化向量模型
# 密钥由 settings 从绝对路径的 .env 读出后显式传入，不依赖进程环境变量与启动目录
_embeddings = DashScopeEmbeddings(
    model=settings.rag.embedding_model,
    dashscope_api_key=settings.rag.dashscope_api_key,
)

# 2.初始化VectorStore
_vector_store = Milvus(
    embedding_function=_embeddings,
    collection_name="insurance_collection",
    builtin_function=BM25BuiltInFunction(
        analyzer_params={"type": "chinese"}
    ),
    vector_field=["dense", "sparse"],
    connection_args={"uri": settings.rag.milvus_url},
    auto_id=True,
)

# 3.创建模块级Pipeline和Retriever
pipeline = RAGPipeline(_vector_store)
retriever = ParentChunkRetriever(_vector_store)


def close_rag() -> None:
    """关闭RAG组件"""
    pipeline.close()
    _vector_store.client.close()
# 控制通配符导入，当使用import * 时，也只会导入这3个
__all__ = ['pipeline', 'retriever', 'close_rag']