from langchain_core.messages import AIMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.types import Command

from app.agents.schemas import InsuranceAgentState, Intent
from app.core import get_logger

logger = get_logger(__name__)
# 一、定义节点

# 1.路由节点
async def route_node(state: InsuranceAgentState) -> Command[Intent]:
    previous_workflow = state.get("previous_workflow", "")
    intent = "chitchat"
    return Command(
        update={
            "previous_workflow": previous_workflow,
            "active_workflow": intent
        },
        goto=intent,
    )

# 2.闲聊节点
async def chitchat_node(state: InsuranceAgentState) -> dict:
    return {"messages": [AIMessage("你好，今天想聊点什么？")]}

# 3.保险推荐节点
async def recommendation_node(state: InsuranceAgentState) -> dict:
    return {"messages": [AIMessage("推荐节点暂未开通")]}

# 4.理赔节点
async def claim_node(state: InsuranceAgentState) -> dict:
    return {"messages": [AIMessage("已记录转人工请求，后续可接入人工客服系统。")]}


# 5.人工节点
async def human_handoff_node(state: InsuranceAgentState) -> dict:
    return {"messages": [AIMessage("人工节点暂未开通")]}

# 6.fallback节点
async def fallback_node(state: InsuranceAgentState) -> dict:
    return {"messages": [AIMessage("我还不能确定你的需求，请说明是想咨询保险、推荐方案还是办理理赔。")]}


# 二、定义主graph
def init_insurance_orchestrator(checkpointer: AsyncPostgresSaver) -> StateGraph:
    """初始化保险顾问主Graph"""

    builder = StateGraph(InsuranceAgentState)
    builder.add_node("route", route_node)
    builder.add_node("chitchat", chitchat_node)
    builder.add_node("recommendation_plan", recommendation_node)
    builder.add_node("claim", claim_node)
    builder.add_node("human_handoff", human_handoff_node)
    builder.add_node("fallback", fallback_node)

    builder.add_edge(START, "route")
    builder.add_edge("chitchat", END)
    builder.add_edge("recommendation_plan", END)
    builder.add_edge("claim", END)
    builder.add_edge("human_handoff", END)
    builder.add_edge("fallback", END)

    return builder.compile()
