from sqlalchemy.ext.asyncio import AsyncSession

from .models import ChatThread
from .repository import ChatThreadRepository
from .. import chat_thread


class ChatThreadService:
    def __init__(self, session:AsyncSession):
        self.session = session
        self.repository = ChatThreadRepository(session)

    async def add(self, user_id: int, title: str):
        """创建会话"""
        # 用上下文管理，开启事务，运行完成，自动commit，出现异常，自动rollback
        async with self.session.begin():
            chat_thread = ChatThread(user_id=user_id, title=title)
            await self.repository.add(chat_thread)
            return chat_thread
