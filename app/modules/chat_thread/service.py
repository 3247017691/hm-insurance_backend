from sqlalchemy.ext.asyncio import AsyncSession

from .models import ChatThread
from .repository import ChatThreadRepository
from .schemas import ChatThreadResponse


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

    async def get_by_user_id(self, user_id: int) -> list[ChatThreadResponse]:
        """查询指定用户拥有的全部会话，按更新时间倒序"""
        threads = await self.repository.get_by_user_id(user_id=user_id)
        return [ChatThreadResponse.model_validate(t) for t in threads]
