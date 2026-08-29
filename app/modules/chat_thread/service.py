from uuid import UUID

from fastapi import HTTPException
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import ChatThreadNotFoundError
from .models import ChatThread
from .repository import ChatThreadRepository
from .schemas import ChatMessageResponse, ChatThreadMessagesResponse, ChatThreadResponse


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
            thread = await self.repository.find_owned(thread_id=thread_id, user_id=user_id)
            if thread is None:
                raise ChatThreadNotFoundError
            await self.repository.delete(thread)

    async def get_messages(
            self,
            thread_id: UUID,
            user_id: int,
            agent: CompiledStateGraph,
    ) -> ChatThreadMessagesResponse:
        """查询指定会话的历史消息与 interrupt 状态，消息由 LangGraph Checkpointer 持久化"""
        # 1.校验会话是否属于当前用户，避免泄露其他用户的会话消息
        thread = await self.repository.find_owned(thread_id=thread_id, user_id=user_id)
        if thread is None:
            raise ChatThreadNotFoundError

        # 2.从 Checkpointer 读取会话状态，无历史记录时返回空数组而非报错
        config = {'configurable': {'thread_id': str(thread_id)}}
        state = await agent.aget_state(config)
        if state is None:
            return ChatThreadMessagesResponse(thread_id=thread_id, messages=[], interrupt=None)

        # 3.只保留 user/assistant 消息，过滤工具调用消息；human/ai 映射为前端期望的 user/assistant
        role_map = {'human': 'user', 'ai': 'assistant'}
        messages: list[ChatMessageResponse] = []
        for message in state.values.get('messages', []):
            role = role_map.get(message.type)
            if role is None:
                continue
            content = message.content if isinstance(message.content, str) else str(message.content)
            if not content.strip():
                continue
            messages.append(ChatMessageResponse(role=role, content=content))

        # 4.提取当前未处理的中断确认信息（如人工确认保险方案），无中断时为 None
        interrupt = None
        if state.next:
            for task in state.tasks:
                if task.interrupts:
                    interrupt = task.interrupts[0].value
                    break

        return ChatThreadMessagesResponse(
            thread_id=thread_id,
            messages=messages,
            interrupt=interrupt,
        )

