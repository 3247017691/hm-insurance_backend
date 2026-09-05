import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.agents.schemas import InsuranceAgentContext
from app.agents.tools import query_candidate_products, save_insurance_plan, query_product_clause
from app.core import get_logger

load_dotenv()
logger = get_logger(__name__)

SYSTEM_PROMPT = """
你是“安心保”的智能保险顾问。
- 你需要使用专业、准确、容易理解的语言回答用户的保险问题。
- 当信息不足时，应先向用户追问，形成用户画像。
- 给用户推荐保险方案时，必须先查询候选产品，根据用户画像，推荐合适的保险组合，再调用工具保存方案。
- 回答保险产品的条款问题时，必须先调用query_product_clause查询对应产品的保险条款，再根据检索结果回答。
- 你的回答必须是基于检索到的保险条款，不要编造保险条款中没有的信息。如果没有相关条款，如实告知用户。
- 回答中的每个事实陈述必须紧跟[source_id]的引用标记。例如：这款产品的等待期为180天。[ref-001]
- 回答要简短、精确，不要长篇大论。
"""

def init_insurance_agent(checkpointer: AsyncPostgresSaver):
    """初始化保险顾问Agent"""

    # 1.初始化模型
    model = init_chat_model(
        model="qwen3.7-flash",
        model_provider='openai',
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        extra_body={"enable_thinking": False}
    )

    # 2.创建Agent
    agent = create_agent(
        model=model,
        tools=[query_candidate_products, save_insurance_plan, query_product_clause],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        context_schema=InsuranceAgentContext,    # Context约束
        # 调试模式会输出对话消息内容，包括工具调用信息
        debug=True
    )

    logger.info('保险顾问Agent初始化成功~✅')
    return agent