from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import get_session
from app.modules.chat_thread.schemas import (
    ChatThreadCreate,
    ChatThreadResponse,
    ChatThreadUpdate,
)
from app.modules.chat_thread.service import ChatThreadService

router = APIRouter(prefix="/api/v1/chat-threads", tags=["会话管理"])

def get_service(session:AsyncSession = Depends(get_session)):
    return ChatThreadService(session)


@router.post("", response_model=ChatThreadResponse, tags=["会话管理"])
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


@router.patch(
    "/{thread_id}",
    response_model=ChatThreadResponse,
    summary="重命名会话",
    description="修改指定会话的标题，会话不存在或不属于当前用户时统一返回会话不存在",
)
async def update_chat_thread(
        thread_id: UUID,
        request: ChatThreadUpdate,
        user_id: Annotated[int, Header(alias="x-user-id")],
        service: ChatThreadService = Depends(get_service),
) -> ChatThreadResponse:
    """重命名会话"""
    return await service.update(thread_id, user_id, request.title)


@router.delete(
    "/{thread_id}",
    summary="删除会话",
    description="删除指定会话，会话不存在或不属于当前用户时统一返回会话不存在",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_chat_thread(
        thread_id: UUID,
        user_id: Annotated[int, Header(alias="x-user-id")],
        service: ChatThreadService = Depends(get_service),
) -> None:
    """删除会话"""
    await service.delete(thread_id, user_id)
