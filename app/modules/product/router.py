from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import get_session
from app.modules.product.schemas import ProductResponse
from app.modules.product.service import ProductService

router = APIRouter(prefix="/api/v1/products", tags=["保险产品"])



@router.get("", response_model=list[ProductResponse], summary="查询保险产品列表", description="按分类查询保险产品列表")
async def list_products(
    category: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[ProductResponse]:
    # 1.获取Service
    service = ProductService(session)
    # 2.查询并返回产品列表
    return await service.list_products(category)


@router.get(
    "/candidates",
    response_model=list[ProductResponse],
    summary="查询候选保险产品",
    description="按险种和保费条件查询可用于推荐的候选保险产品",
)
async def get_candidates(
    categories: Annotated[list[str], Query(description="产品分类，可传多个")],
    session: Annotated[AsyncSession, Depends(get_session)],
    premium_min: Annotated[
        Decimal | None,
        Query(description="只返回最低保费小于该值的产品"),
    ] = None,
    limit_per_category: Annotated[
        int,
        Query(ge=1, description="每个险种最多返回数量"),
    ] = 5,
) -> list[ProductResponse]:
    service = ProductService(session)
    return await service.get_candidates(
        categories=categories,
        premium_min=premium_min,
        limit_per_category=limit_per_category,
    )
