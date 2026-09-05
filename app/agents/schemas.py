from typing import Literal
from dataclasses import dataclass
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

Intent = Literal[
    "chitchat",
    "recommendation_plan",
    "claim",
    "human_handoff",
    "fallback",
]

class RouteResult(BaseModel):
    """意图识别结果"""

    intent: Intent = Field(description="本轮消息应进入的工作流")
    reason: str = Field(description="判断该意图的理由")

class InsuranceAgentState(MessagesState):
    """保险主图的状态"""

    previous_workflow: Intent
    active_workflow: Intent

@dataclass(frozen=True)
class InsuranceAgentContext:
    """保险顾问Agent运行时上下文"""
    user_id: int