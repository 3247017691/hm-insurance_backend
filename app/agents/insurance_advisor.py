from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app import settings
from app.agents.tools import query_candidate_products
from app.core import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT="""
你是"安心保"的智能顾问。
你需要使用专业、准确、容易理解的语言进行回答用户的保险问题。
当信息不足时，应先想用户追问，不要编造保险产品或保障内容。
"""

def init_insurance_agent(checkpointer: AsyncPostgresSaver):
    """初始化保险顾问Agent"""

    # 1.初始化模型
    model = init_chat_model(
        model=settings.llm.chat_model,
        api_key=settings.llm.api_key,
        extra_body={'thinking':{'type':'disabled'}}
    )

    # 2.创建Agent
    agent = create_agent(
        model=model,
        tools=[query_candidate_products],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer
    )

    logger.info('保险顾问Agent初始化成功~✅')
    return agent