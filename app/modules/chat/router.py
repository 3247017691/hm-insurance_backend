from typing import Annotated

from fastapi import APIRouter, Request
from fastapi import Depends
from fastapi.params import Header
from fastapi.sse import EventSourceResponse, ServerSentEvent
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import get_session
from app.modules.chat.schemas import ChatRequest
from app.modules.chat.service import ChatService

router = APIRouter(prefix='/api/v1/chat', tags=["智能助手"])


def get_chat_service(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    agent = request.app.state.agent
    return ChatService(session,agent)

@router.post('', response_class=EventSourceResponse, summary='智能客服对话')
async def chat(
        request: ChatRequest,
        user_id: Annotated[int, Header(alias="x-user-id")],
        service: ChatService = Depends(get_chat_service),
):
    async for see in service.chat_stream(user_id, request):
        yield see