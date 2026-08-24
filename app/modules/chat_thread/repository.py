from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat_thread.models import ChatThread


class ChatThreadRepository:
    def __init__(self, session:AsyncSession):
        self.session = session
    pass

    async def add(self, chat_thread:ChatThread):
        """添加会话"""
        self.session.add(chat_thread)