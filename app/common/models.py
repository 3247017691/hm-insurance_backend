from typing import Optional
import datetime
import decimal

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Index, Numeric, PrimaryKeyConstraint, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class Products(Base):
    __tablename__ = 'products'
    __table_args__ = (
        CheckConstraint("category::text = ANY (ARRAY['medical'::character varying, 'critical_illness'::character varying, 'accident'::character varying, 'life'::character varying]::text[])", name='chk_products_category'),
        PrimaryKeyConstraint('id', name='products_pkey'),
        Index('idx_products_category', 'category'),
        Index('idx_products_status', 'status'),
        {'comment': '保险商城在售及历史保险产品'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment='产品主键')
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment='商城展示名称')
    clause_name: Mapped[str] = mapped_column(String(300), nullable=False, comment='主条款文件名，包含 .pdf 后缀')
    category: Mapped[str] = mapped_column(String(50), nullable=False, comment='险种分类：医疗、重疾、意外或寿险')
    insurer: Mapped[str] = mapped_column(String(120), nullable=False, comment='承保保险公司')
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'active'::character varying"), comment='产品状态')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='最后更新时间')
    image_url: Mapped[Optional[str]] = mapped_column(Text, comment='产品展示图片地址')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='产品简介')
    min_premium: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(14, 2), comment='产品公开的最低年缴保费参考')
    max_premium: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(14, 2), comment='产品公开的最高保费参考，可为空')
    target_group: Mapped[Optional[str]] = mapped_column(String(300), comment='适用人群说明')
    highlights: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text()), comment='产品亮点列表')
