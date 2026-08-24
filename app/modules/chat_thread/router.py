from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import get_session
from app.modules.chat_thread.schemas import ChatThreadCreate
from app.modules.chat_thread.service import ChatThreadService
from fastapi import Header
from typing import Annotated

router = APIRouter(prefix="/api/v1/chat-threads", tags=["会话管理"])

def get_service(session:AsyncSession = Depends(get_session)):
    return ChatThreadService(session)

@router.post("")
async def create_chat_threads(
        request: ChatThreadCreate,
        user_id: Annotated[int, Header(alias="x-user-id")],
        service: ChatThreadService = Depends(get_service),
):
    return await service.add(user_id, request.title)