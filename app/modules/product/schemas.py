from decimal import Decimal

from pydantic import BaseModel


class ProductResponse(BaseModel):
    # 保险产品相应结果
    id: int
    name: str
    clause_name: str
    category: str
    insurer: str
    image_url: str | None
    description: str | None
    min_premium: Decimal | None
    max_premium: Decimal | None
    target_group: str | None
    highlights: list[str] | None
    status: str