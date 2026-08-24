from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat_thread.models import ChatThread


class ChatThreadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, chat_thread: ChatThread):
        """添加会话"""
        self.session.add(chat_thread)

    async def get_by_user_id(self, user_id: int) -> list[ChatThread]:
        """查询指定用户拥有的全部会话，按更新时间倒序"""
        stmt = (
            select(ChatThread)
            .where(ChatThread.user_id == user_id)
            .order_by(ChatThread.updated_at.desc())
        )
        result = await self.session.scalars(stmt)
        return list(result)

    async def get_by_id(self, thread_id: UUID, user_id: int) -> ChatThread | None:
        """查询指定用户的指定会话，会话不存在或不属于该用户时返回 None"""
        stmt = (
            select(ChatThread)
            .where(ChatThread.user_id == user_id)
            .where(ChatThread.id == thread_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update(self, chat_thread: ChatThread):
        """更新会话，刷新到数据库，事务由 service 层管理"""
        await self.session.flush()

    async def delete(self,thread: ChatThread) -> None:
        """删除会话"""
        await self.session.delete(thread)