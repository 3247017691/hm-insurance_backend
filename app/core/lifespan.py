from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import settings
from app.agents.insurance_advisor import init_insurance_agent
from app.infra.checkpointer import init_checkpointer, close_checkpointer
from app.infra.database import check_database, close_database, logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f'[{settings.app.name}]应用启动中...')

    try:
        # 1.检查业务数据库连接
        await check_database()
        # 2.初始化checkpointer
        checkpointer = await init_checkpointer()
        # 3.初始化保险顾问Agent
        app.state.agent = init_insurance_agent(checkpointer)
        yield
    finally:
        logger.info("应用关闭中")
        # 4.关闭Checkpointer连接池
        await close_checkpointer()
        # 5.关闭SQLAlchemy连接池
        await close_database()
