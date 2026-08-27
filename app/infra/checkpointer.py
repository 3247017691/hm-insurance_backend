from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app import settings
from app.core import get_logger

logger = get_logger(__name__)

# 0.创建checkpointer专用连接池
checkpoint_pool = AsyncConnectionPool(
    conninfo=settings.db.checkpoint_url,
    min_size=1,
    max_size=5,
    kwargs={
        "autocommit": True,
        'prepare_threshold':0,
        'row_factory': dict_row
    },
    open=False
)

async def init_checkpointer() -> AsyncPostgresSaver:
    """初始化checkpointer"""

    # 1.初始化连接池
    await checkpoint_pool.open()
    await checkpoint_pool.wait()

    # 2.创建checkpointer
    checkpoint = AsyncPostgresSaver(checkpoint_pool)
    await checkpoint.setup()
    logger.info("Checkpointer初始化成功~✅")
    return checkpoint


async def close_checkpointer() -> None:
    await checkpoint_pool.close()
    logger.info("Checkpointer连接池已关闭")