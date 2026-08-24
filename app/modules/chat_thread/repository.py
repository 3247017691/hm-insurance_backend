from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat_thread.models import ChatThread


class ChatThreadRepository:
    def __init__(self, session:AsyncSession):
        self.session = session
    pass

    async def add(self, chat_thread:ChatThread):
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