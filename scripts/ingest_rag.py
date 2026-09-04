"""RAG 知识库离线入库脚本。

流程：初始化 Embedding 模型与 Milvus 向量库 → 注入 RAGPipeline →
查询全部在售产品 → 逐产品调用 Pipeline 完成条款解析、父子块切分与入库。

用法（项目根目录下执行）：
    .venv/Scripts/python.exe scripts/ingest_rag.py
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# 允许以脚本方式直接运行：把项目根目录加入 sys.path，否则无法导入 app 包
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# DashScopeEmbeddings 是读取进程环境变量拿密钥的，而 pydantic-settings 只把 .env
# 读进配置对象、不会回写环境变量，所以必须在构造 Embeddings 之前先注入 .env
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_milvus import BM25BuiltInFunction, Milvus

from app.core import configure_logging, get_logger
from app.core.config import settings
from app.infra.database import AsyncSessionFactory, close_database
from app.modules.product.models import Product
from app.modules.product.service import ProductService
from app.rag.pipeline import RAGPipeline

logger = get_logger(__name__)

# 向量模型与查询侧 app.rag 共用同一配置，避免写入与检索模型不一致导致向量语义不兼容
EMBEDDING_MODEL = settings.rag.embedding_model
COLLECTION_NAME = "insurance_collection"

# httpx 默认 trust_env=True，会读这些环境变量作为代理
PROXY_ENV_KEYS = (
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "all_proxy",
)


def use_direct_connection() -> None:
    """绕开终端里残留的代理变量，强制直连。

    MinerU / DashScope / DeepSeek 均为国内端点，本机直连可用；而本地代理客户端一旦
    上游节点失效，就会出现 [SSL: UNEXPECTED_EOF_WHILE_READING]（CONNECT 建好后
    TLS 握手被切断），表现为 MinerU 已经解析完但拉不回结果 zip。
    """
    cleared = [key for key in PROXY_ENV_KEYS if os.environ.pop(key, None)]
    if cleared:
        logger.info(f"已强制直连，清掉代理环境变量: {cleared}")


def quiet_sqlalchemy_echo() -> None:
    """关掉 SQL 回显。

    app.infra.database 中 echo=True 会给 sqlalchemy.engine 挂一个自带格式的 handler，
    而 engine 在本脚本导入阶段就建好了，所以在这里覆盖它的 handler 与日志级别。
    """
    engine_logger = logging.getLogger("sqlalchemy.engine")
    engine_logger.handlers.clear()
    engine_logger.setLevel(logging.WARNING)


def build_vector_store() -> Milvus:
    """初始化 Embedding 模型与 Milvus 向量库。

    langchain_milvus 构造时并不创建集合，首次写入才按子块数据建集合，
    且 drop_old 默认为 False，因此重复执行本脚本不会误删已有向量。
    """
    embeddings = DashScopeEmbeddings(model=EMBEDDING_MODEL)

    return Milvus(
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
        # BM25 中文分词产出 sparse 向量，与 dense 向量组成混合检索
        builtin_function=BM25BuiltInFunction(analyzer_params={"type": "chinese"}),
        vector_field=["dense", "sparse"],
        connection_args={"uri": settings.rag.milvus_url},
        auto_id=True,
    )


async def list_all_products() -> list[Product]:
    """查询全部在售产品。

    单独使用一个 session，查询完即归还连接，避免整个入库期间空占连接。
    """
    async with AsyncSessionFactory() as session:
        service = ProductService(session)
        return await service.list_products()


async def ingest_products(vector_store: Milvus, products: list[Product]) -> list[str]:
    """逐产品构建知识库，返回入库失败的产品名列表。

    父块写 PostgreSQL、子块写 Milvus 均由 Pipeline 内部完成。
    """
    pipeline = RAGPipeline(vector_store)
    failed: list[str] = []
    total = len(products)

    try:
        for index, product in enumerate(products, start=1):
            tag = f"({index}/{total}) 产品 id={product.id} name={product.name}"
            logger.info(f"{tag} 开始入库")
            try:
                await pipeline.ingest(product)
            except Exception:
                # 单个产品失败不影响其余产品，脚本可直接重跑
                logger.error(f"{tag} 入库失败", exc_info=True)
                failed.append(product.name)
            else:
                logger.info(f"{tag} 入库完成")
    finally:
        pipeline.close()

    return failed


async def main() -> int:
    """脚本入口，返回进程退出码：无在售产品或存在入库失败的产品时返回 1。"""
    configure_logging(settings.log.level)
    quiet_sqlalchemy_echo()
    use_direct_connection()

    try:
        logger.info(f"开始构建 RAG 知识库，向量集合: {COLLECTION_NAME}，Milvus: {settings.rag.milvus_url}")

        products = await list_all_products()
        if not products:
            logger.warning("未查询到在售产品，知识库构建终止")
            return 1
        logger.info(f"共查询到 {len(products)} 个在售产品")

        vector_store = build_vector_store()
        failed = await ingest_products(vector_store, products)

        if failed:
            logger.error(f"知识库构建结束，{len(failed)} 个产品失败: {failed}")
            return 1
        logger.info("RAG 知识库构建完成✅️")
        return 0
    finally:
        # 与应用 lifespan 一致，退出前释放数据库连接池
        await close_database()


def run() -> int:
    """Windows 下沿用项目的 Selector 事件循环约定，避免 asyncpg 与默认事件循环不兼容。"""
    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    with asyncio.Runner(loop_factory=loop_factory) as runner:
        return runner.run(main())


if __name__ == "__main__":
    sys.exit(run())
