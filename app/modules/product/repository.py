from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.product.models import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_id_category(
        self,
        category: str | None,
    ) -> list[Product]:
        # 1.组装查询条件：默认只查询active状态的产品
        stmt = select(Product).where(Product.status == "active")
        # 2.如果有category，则追加category过滤（多次调用where默认是AND关系）
        if category is not None:
            stmt = stmt.where(Product.category == category)

        # 3.查询产品列表
        products = await self.session.scalars(
            stmt.order_by(Product.id.asc())
        )
        return list(products)

    async def get_candidates(
        self,
        category: str,
        premium_min: Decimal | None = None,
        limit: int = 5,
    ) -> list[Product]:
        """按单个险种查询可用于推荐的候选产品

        :param category: 产品分类
        :param premium_min: 只返回最低保费小于该值的产品
        :param limit: 最多返回数量
        """
        # 必须条件：产品在售 + 指定险种（多次调用where默认是AND关系）
        stmt = select(Product).where(
            Product.status == "active",
            Product.category == category,
        )
        # 传入了保费阈值时，追加最低保费过滤条件
        if premium_min is not None:
            stmt = stmt.where(Product.min_premium < premium_min)

        result = await self.session.execute(stmt.limit(limit))
        return list(result.scalars().all())
