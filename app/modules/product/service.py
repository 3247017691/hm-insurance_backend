from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.product.models import Product
from app.modules.product.repository import ProductRepository


class ProductService:
    """保险产品业务逻辑"""
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ProductRepository(session)

    async def list_products(self, category: str | None = None ):
        """
        按分类查询产品列表
        :param category: 产品分类
        :return: 产品列表
        """
        return await self.repository.find_by_category(category)

    async def list_products_by_category(
        self,
        categories: list[str],
        premium_min: Decimal | None = None,
        limit_per_category: int = 5,
    ) -> list[Product]:
        """按险种和保费条件查询可用于推荐的候选产品

        :param categories: 产品分类列表，可传多个险种
        :param premium_min: 只返回最低保费小于该值的产品
        :param limit_per_category: 每个险种最多返回数量
        """
        products: list[Product] = []
        # 逐个险种查询，每个险种独立限制返回数量
        for category in categories:
            candidates = await self.repository.find_limit_by_category(
                category=category,
                premium_min=premium_min,
                limit=limit_per_category,
            )
            # 合并各险种的查询结果
            products.extend(candidates)
        return products
