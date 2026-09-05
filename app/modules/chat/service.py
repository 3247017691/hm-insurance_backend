from collections.abc import AsyncIterator
from aiostream import stream as astream
from fastapi.sse import ServerSentEvent
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.stream import CustomTransformer
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.schemas import InsuranceAgentContext
from app.modules.chat.schemas import ChatRequest
from app.modules.chat_thread.exceptions import ChatThreadNotFoundError
from app.modules.chat_thread.repository import ChatThreadRepository
from app.core.logging import get_logger
logger = get_logger(__name__)

class ChatService:
    def __init__(self, session: AsyncSession, agent: CompiledStateGraph):
        self.repository = ChatThreadRepository(session)
        self.agent = agent

    async def chat_stream(
        self,
        user_id: int,
        request: ChatRequest,
    ) -> AsyncIterator[ServerSentEvent]:
        # 1.校验会话是否属于当前用户
        thread = await self.repository.find_owned(
            request.thread_id,
            user_id,
        )
        if thread is None:
            raise ChatThreadNotFoundError

        # 2.校验通过后，调用Agent

        # 2.1.准备Agent输入
        _input = {"messages": [HumanMessage(content=request.message)]}
        config = {"configurable": {"thread_id": str(request.thread_id)}}
        context = InsuranceAgentContext(user_id=user_id)

        # 2.2.使用v3协议获取异步事件流
        stream = await self.agent.astream_events(
            _input,
            config,
            context=context,
            version="v3",
            transformers=[CustomTransformer],
        )

        # 2.3.处理事件流中的messages事件
        async for event in stream:
            method = event['method']
            # 判断事件类型，可以是messages、interrupts等等
            if method == 'messages':
                data = event['params']['data'][0]
                if isinstance(data, AIMessage):
                    yield ServerSentEvent(data=data.text, event="message")
                elif data.get('delta') and data['delta'].get('text'):
                    yield ServerSentEvent(data=data['delta'].get('text'), event="message")

        # 2.4.返回结束标识
        yield ServerSentEvent(data="[DONE]", event="done")