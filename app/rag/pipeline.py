from langchain.chat_models import init_chat_model
from langchain_milvus import Milvus
from langchain_text_splitters import MarkdownHeaderTextSplitter
from mineru import MinerU
from openai import api_key

from app.core import get_logger, settings

logger = get_logger(__name__)


MARKDOWN_OPTIMIZATION_PROMPT  = """
下面这份 Markdown 文档是从保险条款 PDF 解析得来，由于 PDF 中的各个小节是以表格形式存在，所以解析时出现错乱。你分析内容，帮我转为格式正确的 Markdown，特别是标题编号要正确。
- 标题等级要从 1 级标题开始，逐层增加，目录和文档名不计入标题等级。
- 输出结果中不要包含正文开始之前的部分。
- 输出结果只包含 Markdown 正文，不要解释或代码围栏。
- 不要修改保险条款。
""".strip()

class RAGPipeline:
    def __init__(self, vector_store: Milvus) -> None:
        """ 初始化操作：需要使用多次的对象在这里定义
                    使用_定义私有属性，只在内部使用。
        """
        self._vector_store = vector_store

        self._mineru = MinerU(settings.rag.mineru_token)

        self._model = init_chat_model(
            model='deepseek-v4-flash',
            api_key=settings.llm.api_key,
            extra_body={'thinking':{'type':'display'}},
            max_tokens=1000000,
        )

        # 初始化文档切分工具
        self._markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
                ("####", "h4"),
            ]
        )