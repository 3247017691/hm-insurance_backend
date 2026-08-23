from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.product.models import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_category(
            self,
            category: str | None,
    ) -> list[Product]:
        # 1.组装查询条件
        # 1.1.默认只查询active状态的产品
        conditions = [Product.status == "active"]
        # 1.2.如果有category，则添加category过滤
        if category:
            conditions.append(Product.category == category)

        # 2.查询产品列表
        products = await self.session.scalars(
            select(Product)
            .where(*conditions)
            .order_by(Product.id.asc())
        )
        return list(products.all())

    async def find_limit_by_category(
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

        result = await self.session.execute(stmt.order_by(Product.min_premium.asc().nullslast()).limit(limit))
        return list(result.scalars().all())
