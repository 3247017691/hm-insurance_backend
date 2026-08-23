from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import ColumnElement

from app.modules.product.models import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_id_category(
        self,
        category: str | None,
    ) -> list[Product]:
        # 1.组装查询结果
        # 1.1.默认只查询active状态的产品
        conditions = [Product.status == "active"]
        # 1.2.如果有category，则添加category过滤
        if category is not None:
            conditions.append(Product.category == category)

        # 2.查询产品列表
        products = await self.session.scalars(
            select(Product)
            .where(*conditions)
            .order_by(Product.id.asc())
        )
        return list(products)

    async def get_candidates(
        session: AsyncSession,
        category: str,
        premium_min: Decimal | None = None,
        limit: int = 5,
    ) -> list[Product]:
        """按单个险种查询可用于推荐的候选产品

        :param session: 数据库会话
        :param category: 产品分类
        :param premium_min: 只返回最低保费小于该值的产品
        :param limit: 最多返回数量
        """
        # 构建查询条件列表，必须包含：产品在售 + 指定险种
        conditions: list[ColumnElement[bool]] = [
            Product.status == "active",
            Product.category == category,
        ]
        # 传入了保费阈值时，追加最低保费过滤条件
        if premium_min is not None:
            conditions.append(Product.min_premium < premium_min)

        stmt = select(Product).where(*conditions).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())
