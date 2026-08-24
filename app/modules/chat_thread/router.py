from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import get_session
from app.modules.chat_thread.models import ChatThread
from app.modules.chat_thread.schemas import ChatThreadCreate, ChatThreadResponse
from app.modules.chat_thread.service import ChatThreadService
from fastapi import Header
from typing import Annotated

router = APIRouter(prefix="/api/v1/chat-threads", tags=["会话管理"])

def get_service(session:AsyncSession = Depends(get_session)):
    return ChatThreadService(session)

@router.post("", tags=["会话管理"])
async def create_chat_threads(
        request: ChatThreadCreate,
        user_id: Annotated[int, Header(alias="x-user-id")],
        service: ChatThreadService = Depends(get_service),
):
    """创建会话"""
    return await service.add(user_id, request.title)


@router.get(
    "",
    response_model=list[ChatThreadResponse],
    summary="查询会话列表",
    description="查询当前用户拥有的全部对话会话",
)
async def get_chat_threads(
        user_id: Annotated[int, Header(alias="x-user-id")],
        service: ChatThreadService = Depends(get_service),
) -> list[ChatThreadResponse]:
    """查询会话"""
    return await service.get_by_user_id(user_id)
