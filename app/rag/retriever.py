from dotenv import load_dotenv
from langchain_milvus import Milvus
from pymilvus import Function, FunctionType

from app.core import get_logger
from app.infra.database import AsyncSessionFactory
from app.rag.models import ParentChunk
from app.rag.repository import ParentChunkRepository

load_dotenv()
logger = get_logger(__name__)

def create_reranker(query: str) -> Function:
    return Function(
        name='dashscope_smantic_ranker',
        input_field_names=['text'],
        function_type=FunctionType.RERANK,
        params={
            'reranker':'model',
            'provider':'ali',
            'model_name':'qwen3.7-text-rerank',
            "queries": [query],
            "max_client_batch_size": 5,
        }
    )

class ParentChunkRetriever:

    def __init__(self, vector_store: Milvus):
        self.vector_store = vector_store
        logger.info(f"RAG Retriever 初始化完成✅️")

    async def retrieve(self, query: str, product_id: int) -> list[ParentChunk]:

        # 在指定产品内混合检索并重排，得到子块
        child_chunks = await self.vector_store.asimilarity_search(
            query=query,
            k=5,
            fetch_k=10,
            expr=f'product_id == {product_id}',
            reranker=create_reranker(query)
        )

        # 取召回子块携带的 parent_id 并去重，保持精排后的顺序
        parent_ids = list(
            dict.fromkeys(
                [child.metadata['parent_id'] for child in child_chunks]
            )
        )

        # 如果没有召回到父块，则返回空列表
        if not parent_ids:
            return []

        # 根据parent_id批量查询父块
        async with AsyncSessionFactory() as session:
            repository = ParentChunkRepository(session)
            parent_chunks = await repository.list_by_ids(parent_ids)

        # 组装dict[parent_id, parent_chunk]
        parent_chunk_map = {
            str(parent.id): parent
            for parent in parent_chunks
        }

        # 按照召回的parent_ids顺序遍历，再到dict中拿到parent
        return [
            parent_chunk_map[parent_id]  # 推导式的结果
            for parent_id in parent_ids  # 推导式数据来源
        ]