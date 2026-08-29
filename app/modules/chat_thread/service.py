from uuid import UUID

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import ChatThreadNotFoundError
from .models import ChatThread
from .repository import ChatThreadRepository
from .schemas import ChatMessageResponse, ChatHistoryResponse, ChatThreadResponse


class ChatThreadService:
    def __init__(
            self,
            session:AsyncSession,
            agent: CompiledStateGraph
    ):
        self.session = session
        self.repository = ChatThreadRepository(session)
        self.agent = agent

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

    async def update(self, thread_id: UUID, user_id: int, title: str) -> ChatThreadResponse:
        """重命名会话"""
        # 用上下文管理，开启事务，运行完成，自动commit，出现异常，自动rollback
        # 注意：查询必须在 begin() 块内执行，否则 SELECT 会隐式开启事务，再调 begin() 会报 InvalidRequestError
        async with self.session.begin():
            # 1.查询user_id会话
            chat_thread = await self.repository.find_owned(thread_id=thread_id, user_id=user_id)
            # 2.判断user_id的会话是否存在或者是否一致，统一返回会话不存在，避免泄露其他用户的会话信息
            if not chat_thread:
                raise ChatThreadNotFoundError
            # 3.修改会话标题
            chat_thread.title = title
            await self.repository.update(chat_thread)
            # 4.updated_at 由数据库 onupdate=now() 生成，flush 后内存中已过期，
            # 必须显式 refresh 加载最新值，否则序列化时会触发异步懒加载报 MissingGreenlet
            await self.session.refresh(chat_thread)
        return ChatThreadResponse.model_validate(chat_thread)

    async def delete(self, thread_id: UUID, user_id: int) -> None:
        """删除会话"""
        async with self.session.begin():
            # 1.校验会话归属
            thread = await self.repository.find_owned(thread_id=thread_id, user_id=user_id)
            if thread is None:
                raise ChatThreadNotFoundError

            # 2.删除Checkpinter中的会话状态
            await self.agent.checkpointer.adelete_thread(str(thread_id))

            # 3.删除会话元数据
            await self.repository.delete(thread)



    async def get_history(
            self,
            thread_id: UUID,
            user_id: int,
    ) -> ChatHistoryResponse:
        """查询会话历史消息"""
        # 1.校验会话归属
        thread = await self.repository.find_owned(thread_id, user_id)
        if thread is None:
            raise ChatThreadNotFoundError

        # 2.读取Agent最新状态
        config = {"configurable": {"thread_id": str(thread_id)}}
        snapshot = await self.agent.aget_state(config)

        # 3.只保留用户消息和AI消息
        messages = []
        for message in snapshot.values.get("messages", []):
            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            else:
                continue

            if message.text:
                messages.append(ChatMessageResponse(role=role, content=message.text))

        return ChatHistoryResponse(thread_id=thread_id, messages=messages)
