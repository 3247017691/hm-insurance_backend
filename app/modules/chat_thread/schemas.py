from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class  ChatThreadCreate(BaseModel):
    """创建会话请求"""

    title:str = Field(default='新会话', min_length=1, max_length=200)

    @field_validator('title', mode='before')
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return value.strip()


class ChatThreadUpdate(BaseModel):
    """重命名会话请求"""

    title: str = Field(min_length=1, max_length=200)

    @field_validator('title', mode='before')
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return value.strip()


class  ChatThreadResponse(BaseModel):
    """会话响应"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatMessageResponse(BaseModel):
    """会话消息响应"""

    role: str
    content: str
    additional_info: Any | None = None


class ChatThreadMessagesResponse(BaseModel):
    """会话历史消息响应"""

    thread_id: UUID
    messages: list[ChatMessageResponse]
    interrupt: Any | None = None
