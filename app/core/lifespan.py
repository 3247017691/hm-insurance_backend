from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infra.database import check_database, close_database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期管理：启动时检查数据库连接池，关闭时释放连接池"""
    await check_database()
    yield
    await close_database()
