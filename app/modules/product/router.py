from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import get_session
from app.modules.product.schemas import ProductResponse
from app.modules.product.service import ProductService

router = APIRouter(prefix="/api/v1/products", tags=["保险产品"])


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
