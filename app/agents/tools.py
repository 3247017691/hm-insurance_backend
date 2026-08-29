from decimal import Decimal

from fastapi.encoders import jsonable_encoder
from langchain_core.tools import tool

from app.infra.database import AsyncSessionFactory
from app.modules.product.models import Product
from app.modules.product.service import ProductService


@tool
async def query_candidate_products(
    categories: list[str],
    premium_min: Decimal | None = None,
    limit_per_category: int = 5,
):
    """
    根据险种和保费条件查询可用于推荐的候选保险产品。当用户咨询具体保险产品或需要保险产品推荐时使用。

    Args:
        categories: 产品分类列表，可选值为 medical、critical_illness、life、accident。
        premium_min: 最低保费上限，可选参数，只返回最低保费小于该值的产品。
        limit_per_category: 每个险种最多返回的产品数量，可选参数，默认5。
    """
    async with AsyncSessionFactory() as session:
        # 1.初始化session
        service = ProductService(session)
        # 2.调用service,得到候选产品
        products: list[Product] = await service.list_products_by_category(
            categories=categories,
            premium_min=premium_min,
            limit_per_category=limit_per_category,
        )
        # 3.返回结果给AI,最好把Product处理成json返回
        return jsonable_encoder(products)