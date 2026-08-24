from typing import Optional
import datetime
import decimal
import uuid

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKeyConstraint, Index, Integer, Numeric, PrimaryKeyConstraint, String, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class AppMetadata(Base):
    __tablename__ = 'app_metadata'
    __table_args__ = (
        PrimaryKeyConstraint('key', name='app_metadata_pkey'),
        {'comment': '业务服务的数据库元数据与初始化标记'}
    )

    key: Mapped[str] = mapped_column(String(100), primary_key=True, comment='元数据键')
    value: Mapped[str] = mapped_column(Text, nullable=False, comment='元数据值')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')


class ChatThreads(Base):
    __tablename__ = 'chat_threads'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='chat_threads_pkey'),
        Index('idx_chat_threads_user_updated', 'user_id', 'updated_at'),
        {'comment': '用户与智能客服的会话元数据，消息正文由 LangGraph Checkpointer 保存'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, comment='会话主键，同时作为 LangGraph thread_id')
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='JWT 中解析出的业务用户主键')
    title: Mapped[str] = mapped_column(String(200), nullable=False, server_default=text("'新会话'::character varying"), comment='会话列表展示标题')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='会话创建时间')
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='最后一次对话或修改标题的时间')


class InsurerApiAdapters(Base):
    __tablename__ = 'insurer_api_adapters'
    __table_args__ = (
        CheckConstraint("adapter_type::text = ANY (ARRAY['mock'::character varying, 'http'::character varying]::text[])", name='chk_insurer_api_adapters_type'),
        CheckConstraint("status::text = ANY (ARRAY['active'::character varying, 'inactive'::character varying]::text[])", name='chk_insurer_api_adapters_status'),
        PrimaryKeyConstraint('id', name='insurer_api_adapters_pkey'),
        UniqueConstraint('insurer_code', name='insurer_api_adapters_insurer_code_key'),
        {'comment': '保险公司保费试算接口适配器配置'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, comment='适配器主键')
    insurer_code: Mapped[str] = mapped_column(String(80), nullable=False, comment='保险公司适配器编码')
    adapter_type: Mapped[str] = mapped_column(String(40), nullable=False, comment='适配器类型：mock 或 HTTP')
    adapter_name: Mapped[str] = mapped_column(String(120), nullable=False, comment='适配器名称')
    auth_type: Mapped[str] = mapped_column(String(40), nullable=False, server_default=text("'none'::character varying"), comment='接口认证方式')
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='适配器非敏感配置')
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'active'::character varying"), comment='适配器状态')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='最后更新时间')
    base_url: Mapped[Optional[str]] = mapped_column(String(500), comment='保险公司接口基础地址')

    premium_quotes: Mapped[list['PremiumQuotes']] = relationship('PremiumQuotes', back_populates='adapter')
    product_pricing_bindings: Mapped[list['ProductPricingBindings']] = relationship('ProductPricingBindings', back_populates='adapter')


class ParentChunks(Base):
    __tablename__ = 'parent_chunks'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='parent_chunks_pkey'),
        Index('idx_parent_chunks_product', 'product_id'),
        {'comment': '用于完整上下文和引用展示的父知识块'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, comment='父块主键')
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='关联的保险产品主键')
    clause_name: Mapped[str] = mapped_column(String(300), nullable=False, comment='条款文件名，包含 .pdf 后缀')
    section_path: Mapped[list[str]] = mapped_column(ARRAY(Text()), nullable=False, server_default=text('ARRAY[]::text[]'), comment='Markdown 标题层级路径')
    content: Mapped[str] = mapped_column(Text, nullable=False, comment='父块完整正文')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')


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

    policies: Mapped[list['Policies']] = relationship('Policies', back_populates='product')
    product_pricing_schemas: Mapped[list['ProductPricingSchemas']] = relationship('ProductPricingSchemas', back_populates='product')
    rate_plans: Mapped[list['RatePlans']] = relationship('RatePlans', back_populates='product')
    rate_table_files: Mapped[list['RateTableFiles']] = relationship('RateTableFiles', back_populates='product')
    claims: Mapped[list['Claims']] = relationship('Claims', back_populates='product')
    insurance_plan_items: Mapped[list['InsurancePlanItems']] = relationship('InsurancePlanItems', back_populates='product')
    premium_quotes: Mapped[list['PremiumQuotes']] = relationship('PremiumQuotes', back_populates='product')
    product_pricing_bindings: Mapped[list['ProductPricingBindings']] = relationship('ProductPricingBindings', back_populates='product')
    rate_table_items: Mapped[list['RateTableItems']] = relationship('RateTableItems', back_populates='product')


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='users_pkey'),
        UniqueConstraint('email', name='users_email_key'),
        UniqueConstraint('username', name='users_username_key'),
        {'comment': '保险商城用户账户'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment='用户主键')
    username: Mapped[str] = mapped_column(String(80), nullable=False, comment='登录用户名')
    email: Mapped[str] = mapped_column(String(160), nullable=False, comment='用户邮箱')
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment='加密后的登录密码')
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'active'::character varying"), comment='账户状态')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='最后更新时间')
    display_name: Mapped[Optional[str]] = mapped_column(String(100), comment='用户展示名称')

    insurance_plans: Mapped[list['InsurancePlans']] = relationship('InsurancePlans', back_populates='user')
    orders: Mapped[list['Orders']] = relationship('Orders', back_populates='user')
    policies: Mapped[list['Policies']] = relationship('Policies', back_populates='user')
    claims: Mapped[list['Claims']] = relationship('Claims', back_populates='user')
    premium_quotes: Mapped[list['PremiumQuotes']] = relationship('PremiumQuotes', back_populates='user')


class InsurancePlans(Base):
    __tablename__ = 'insurance_plans'
    __table_args__ = (
        CheckConstraint('annual_premium_budget IS NULL OR annual_premium_budget >= 0::numeric', name='chk_insurance_plans_budget'),
        CheckConstraint("status::text = ANY (ARRAY['uninsured'::character varying, 'applying'::character varying, 'insured'::character varying]::text[])", name='chk_insurance_plans_status'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='insurance_plans_user_id_fkey'),
        PrimaryKeyConstraint('id', name='insurance_plans_pkey'),
        Index('idx_insurance_plans_user', 'user_id', 'status'),
        {'comment': '用户保存的保险产品组合方案'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, comment='方案主键')
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='方案所属用户')
    plan_name: Mapped[str] = mapped_column(String(120), nullable=False, comment='方案名称')
    insured_profile: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='推荐时使用的被保险人画像')
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'uninsured'::character varying"), comment='方案投保状态')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='最后更新时间')
    summary: Mapped[Optional[str]] = mapped_column(Text, comment='方案整体说明')
    annual_premium_budget: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(14, 2), comment='组合年缴预算参考')

    user: Mapped['Users'] = relationship('Users', back_populates='insurance_plans')
    insurance_plan_items: Mapped[list['InsurancePlanItems']] = relationship('InsurancePlanItems', back_populates='plan')


class Orders(Base):
    __tablename__ = 'orders'
    __table_args__ = (
        CheckConstraint("status::text = ANY (ARRAY['pending_payment'::character varying, 'pending_policy'::character varying, 'paid'::character varying, 'completed'::character varying, 'cancelled'::character varying]::text[])", name='chk_orders_status'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='orders_user_id_fkey'),
        PrimaryKeyConstraint('id', name='orders_pkey'),
        UniqueConstraint('confirmation_id', name='orders_confirmation_id_key'),
        UniqueConstraint('idempotency_key', name='orders_idempotency_key_key'),
        UniqueConstraint('order_number', name='orders_order_number_key'),
        Index('idx_orders_idempotency', 'idempotency_key'),
        Index('idx_orders_user', 'user_id'),
        {'comment': '单产品投保流程末端创建的商城订单'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, comment='订单主键')
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='下单用户')
    order_number: Mapped[str] = mapped_column(String(40), nullable=False, comment='商城订单号')
    items: Mapped[dict] = mapped_column(JSONB, nullable=False, comment='订单产品和投保信息快照')
    quote_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(Uuid()), nullable=False, server_default=text("'{}'::uuid[]"), comment='订单引用的试算结果')
    total_premium: Mapped[decimal.Decimal] = mapped_column(Numeric(14, 2), nullable=False, comment='订单总保费')
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'pending_payment'::character varying"), comment='订单状态')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='最后更新时间')
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, comment='下单时关联的客服会话，可为空')
    confirmation_id: Mapped[Optional[str]] = mapped_column(String(60), comment='前端最终确认标识')
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(160), comment='防止重复创建订单的幂等键')
    recommendation_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, comment='下单时的推荐方案快照')
    idempotency_fingerprint: Mapped[Optional[str]] = mapped_column(String(64), comment='幂等请求内容指纹')

    user: Mapped['Users'] = relationship('Users', back_populates='orders')


class Policies(Base):
    __tablename__ = 'policies'
    __table_args__ = (
        CheckConstraint("status::text = ANY (ARRAY['pending'::character varying, 'active'::character varying, 'expired'::character varying, 'terminated'::character varying]::text[])", name='chk_policies_status'),
        ForeignKeyConstraint(['product_id'], ['products.id'], name='policies_product_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='policies_user_id_fkey'),
        PrimaryKeyConstraint('id', name='policies_pkey'),
        UniqueConstraint('policy_number', name='policies_policy_number_key'),
        Index('idx_policies_user_status_effective', 'user_id', 'status', 'effective_at'),
        Index('uk_policies_application_no', 'application_no', postgresql_where='(application_no IS NOT NULL)', unique=True),
        {'comment': '用户已承保的教学保单'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, comment='保单主键')
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='保单所属用户')
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='承保产品')
    policy_number: Mapped[str] = mapped_column(String(60), nullable=False, comment='保险公司保单号')
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'active'::character varying"), comment='保单状态')
    effective_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, comment='保单生效时间')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='最后更新时间')
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='保单到期时间')
    application_no: Mapped[Optional[str]] = mapped_column(String(60), comment='投保单号，教学演示中用于串联投保流程')
    holder_name: Mapped[Optional[str]] = mapped_column(String(80), comment='投保人姓名')
    insured_name: Mapped[Optional[str]] = mapped_column(String(80), comment='被保人姓名')
    insured_id_no_masked: Mapped[Optional[str]] = mapped_column(String(40), comment='被保人证件号脱敏展示')
    insured_phone: Mapped[Optional[str]] = mapped_column(String(40), comment='被保人联系电话')
    coverage_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(14, 2), comment='本保单教学演示保额')
    premium_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(14, 2), comment='本保单教学演示保费')
    payment_frequency: Mapped[Optional[str]] = mapped_column(String(30), comment='缴费频率，例如 annual')
    beneficiary: Mapped[Optional[dict]] = mapped_column(JSONB, comment='受益人信息快照')
    policy_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, comment='投保当时产品、方案、推荐理由等信息快照')
    coverage_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, comment='理赔演示使用的保障责任摘要快照')
    paid_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='支付完成时间')
    issued_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='承保出单时间')

    product: Mapped['Products'] = relationship('Products', back_populates='policies')
    user: Mapped['Users'] = relationship('Users', back_populates='policies')
    claims: Mapped[list['Claims']] = relationship('Claims', back_populates='policy')


class ProductPricingSchemas(Base):
    __tablename__ = 'product_pricing_schemas'
    __table_args__ = (
        CheckConstraint("status::text = ANY (ARRAY['draft'::character varying, 'active'::character varying, 'inactive'::character varying]::text[])", name='chk_product_pricing_schemas_status'),
        ForeignKeyConstraint(['product_id'], ['products.id'], name='product_pricing_schemas_product_id_fkey'),
        PrimaryKeyConstraint('id', name='product_pricing_schemas_pkey'),
        UniqueConstraint('product_id', 'scenario', 'schema_version', name='uk_product_pricing_schema_version'),
        Index('idx_product_pricing_schemas_product', 'product_id', 'scenario', 'status'),
        {'comment': '产品动态保费试算表单定义'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, comment='试算模板主键')
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属产品')
    scenario: Mapped[str] = mapped_column(String(80), nullable=False, server_default=text("'premium_by_coverage'::character varying"), comment='试算业务场景')
    schema_version: Mapped[str] = mapped_column(String(80), nullable=False, comment='模板版本')
    schema_json: Mapped[dict] = mapped_column(JSONB, nullable=False, comment='前端动态表单 JSON Schema')
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'draft'::character varying"), comment='模板状态')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    schema_hash: Mapped[Optional[str]] = mapped_column(String(64), comment='模板内容哈希')
    activated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='启用时间')

    product: Mapped['Products'] = relationship('Products', back_populates='product_pricing_schemas')
    premium_quotes: Mapped[list['PremiumQuotes']] = relationship('PremiumQuotes', back_populates='pricing_schema')
    product_pricing_bindings: Mapped[list['ProductPricingBindings']] = relationship('ProductPricingBindings', back_populates='pricing_schema')


class RatePlans(Base):
    __tablename__ = 'rate_plans'
    __table_args__ = (
        CheckConstraint("rate_type::text = ANY (ARRAY['fixed_plan_premium'::character varying, 'age_band_plan_premium'::character varying, 'per_1000_sum_assured'::character varying, 'per_10000_sum_assured'::character varying, 'coverage_amount_matrix'::character varying, 'rider_rate'::character varying]::text[])", name='chk_rate_plans_type'),
        CheckConstraint("status::text = ANY (ARRAY['active'::character varying, 'inactive'::character varying]::text[])", name='chk_rate_plans_status'),
        ForeignKeyConstraint(['product_id'], ['products.id'], name='rate_plans_product_id_fkey'),
        PrimaryKeyConstraint('id', name='rate_plans_pkey'),
        UniqueConstraint('product_id', 'plan_code', name='uk_rate_plans_product_code'),
        {'comment': '产品费率计划及试算参数定义'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, comment='费率计划主键')
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属产品')
    plan_code: Mapped[str] = mapped_column(String(80), nullable=False, comment='产品内唯一的计划编码')
    plan_name: Mapped[str] = mapped_column(String(200), nullable=False, comment='计划展示名称')
    rate_type: Mapped[str] = mapped_column(String(50), nullable=False, comment='费率计算类型')
    currency: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'CNY'::character varying"), comment='保费币种')
    required_params: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"), comment='必填试算参数定义')
    optional_params: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"), comment='可选试算参数定义')
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'active'::character varying"), comment='计划状态')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='最后更新时间')

    product: Mapped['Products'] = relationship('Products', back_populates='rate_plans')


class RateTableFiles(Base):
    __tablename__ = 'rate_table_files'
    __table_args__ = (
        CheckConstraint("status::text = ANY (ARRAY['pending'::character varying, 'parsed'::character varying, 'validated'::character varying, 'active'::character varying, 'failed'::character varying]::text[])", name='chk_rate_table_files_status'),
        ForeignKeyConstraint(['product_id'], ['products.id'], name='rate_table_files_product_id_fkey'),
        PrimaryKeyConstraint('id', name='rate_table_files_pkey'),
        {'comment': '从保险公司费率文件抽取的文件级记录'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, comment='费率文件主键')
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属产品')
    file_name: Mapped[str] = mapped_column(String(300), nullable=False, comment='费率文件名')
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, comment='费率文件路径')
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'::character varying"), comment='解析和校验状态')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), comment='文件内容哈希')
    parser_version: Mapped[Optional[str]] = mapped_column(String(50), comment='解析器版本')
    validation_report: Mapped[Optional[dict]] = mapped_column(JSONB, comment='结构化校验报告')
    activated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='启用时间')

    product: Mapped['Products'] = relationship('Products', back_populates='rate_table_files')
    rate_table_items: Mapped[list['RateTableItems']] = relationship('RateTableItems', back_populates='rate_file')


class Claims(Base):
    __tablename__ = 'claims'
    __table_args__ = (
        CheckConstraint("claim_type::text = ANY (ARRAY['medical'::character varying, 'accident'::character varying, 'critical_illness'::character varying, 'life'::character varying]::text[])", name='chk_claims_type'),
        CheckConstraint("status::text = ANY (ARRAY['submitted'::character varying, 'reviewing'::character varying, 'approved'::character varying, 'rejected'::character varying, 'paid'::character varying]::text[])", name='chk_claims_status'),
        ForeignKeyConstraint(['policy_id'], ['policies.id'], name='claims_policy_id_fkey'),
        ForeignKeyConstraint(['product_id'], ['products.id'], name='claims_product_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='claims_user_id_fkey'),
        PrimaryKeyConstraint('id', name='claims_pkey'),
        Index('idx_claims_user', 'user_id'),
        Index('idx_claims_user_policy_updated', 'user_id', 'policy_id', 'updated_at'),
        Index('uk_claims_claim_number', 'claim_number', postgresql_where='(claim_number IS NOT NULL)', unique=True),
        {'comment': '用户理赔案件及查询进度'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, comment='理赔案件主键')
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='案件所属用户')
    claim_type: Mapped[str] = mapped_column(String(50), nullable=False, comment='理赔险种类型')
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'submitted'::character varying"), comment='理赔处理状态')
    submitted_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='理赔申请时间')
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='进度最后更新时间')
    product_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='关联保险产品')
    amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(14, 2), comment='案件已申请或已赔付金额，可为空')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='案件说明')
    policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, comment='关联保单')
    claim_number: Mapped[Optional[str]] = mapped_column(String(60), comment='保险公司理赔案件号')

    policy: Mapped[Optional['Policies']] = relationship('Policies', back_populates='claims')
    product: Mapped[Optional['Products']] = relationship('Products', back_populates='claims')
    user: Mapped['Users'] = relationship('Users', back_populates='claims')


class InsurancePlanItems(Base):
    __tablename__ = 'insurance_plan_items'
    __table_args__ = (
        CheckConstraint('annual_premium_budget IS NULL OR annual_premium_budget >= 0::numeric', name='chk_insurance_plan_items_budget'),
        CheckConstraint('priority >= 1', name='insurance_plan_items_priority_check'),
        CheckConstraint("status::text = ANY (ARRAY['uninsured'::character varying, 'insured'::character varying]::text[])", name='chk_insurance_plan_items_status'),
        ForeignKeyConstraint(['plan_id'], ['insurance_plans.id'], ondelete='CASCADE', name='insurance_plan_items_plan_id_fkey'),
        ForeignKeyConstraint(['product_id'], ['products.id'], name='insurance_plan_items_product_id_fkey'),
        PrimaryKeyConstraint('id', name='insurance_plan_items_pkey'),
        UniqueConstraint('plan_id', 'product_id', name='uk_insurance_plan_items_plan_product'),
        Index('idx_insurance_plan_items_plan', 'plan_id', 'status'),
        {'comment': '保险组合方案中的产品项'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, comment='方案项主键')
    plan_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, comment='所属保险方案')
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='推荐产品')
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='方案内展示顺序')
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'uninsured'::character varying"), comment='方案项投保状态')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='最后更新时间')
    recommendation_reason: Mapped[Optional[str]] = mapped_column(Text, comment='推荐该产品的理由')
    annual_premium_budget: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(14, 2), comment='产品年缴预算参考')

    plan: Mapped['InsurancePlans'] = relationship('InsurancePlans', back_populates='insurance_plan_items')
    product: Mapped['Products'] = relationship('Products', back_populates='insurance_plan_items')


class PremiumQuotes(Base):
    __tablename__ = 'premium_quotes'
    __table_args__ = (
        CheckConstraint("pricing_mode::text = ANY (ARRAY['table'::character varying, 'demo_formula'::character varying, 'mock_adapter'::character varying, 'insurer_api'::character varying, 'local_fallback'::character varying]::text[])", name='chk_premium_quotes_pricing_mode'),
        ForeignKeyConstraint(['adapter_id'], ['insurer_api_adapters.id'], name='premium_quotes_adapter_id_fkey'),
        ForeignKeyConstraint(['pricing_schema_id'], ['product_pricing_schemas.id'], name='premium_quotes_pricing_schema_id_fkey'),
        ForeignKeyConstraint(['product_id'], ['products.id'], name='premium_quotes_product_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='premium_quotes_user_id_fkey'),
        PrimaryKeyConstraint('id', name='premium_quotes_pkey'),
        Index('idx_premium_quotes_user', 'user_id'),
        {'comment': '单产品保费试算结果'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, comment='试算结果主键')
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='试算产品')
    request_params: Mapped[dict] = mapped_column(JSONB, nullable=False, comment='原始试算请求参数')
    result: Mapped[dict] = mapped_column(JSONB, nullable=False, comment='统一试算响应')
    total_premium: Mapped[decimal.Decimal] = mapped_column(Numeric(14, 2), nullable=False, comment='试算年缴保费')
    pricing_mode: Mapped[str] = mapped_column(String(30), nullable=False, comment='试算实现方式')
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, comment='试算结果失效时间')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='发起试算的用户')
    pricing_schema_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, comment='使用的试算模板')
    schema_version: Mapped[Optional[str]] = mapped_column(String(80), comment='试算模板版本')
    adapter_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, comment='使用的保险公司适配器')
    answers: Mapped[Optional[dict]] = mapped_column(JSONB, comment='用户填写的动态表单答案')
    external_request: Mapped[Optional[dict]] = mapped_column(JSONB, comment='发送给适配器的请求快照')
    external_response: Mapped[Optional[dict]] = mapped_column(JSONB, comment='适配器原始响应快照')

    adapter: Mapped[Optional['InsurerApiAdapters']] = relationship('InsurerApiAdapters', back_populates='premium_quotes')
    pricing_schema: Mapped[Optional['ProductPricingSchemas']] = relationship('ProductPricingSchemas', back_populates='premium_quotes')
    product: Mapped['Products'] = relationship('Products', back_populates='premium_quotes')
    user: Mapped[Optional['Users']] = relationship('Users', back_populates='premium_quotes')


class ProductPricingBindings(Base):
    __tablename__ = 'product_pricing_bindings'
    __table_args__ = (
        CheckConstraint("status::text = ANY (ARRAY['active'::character varying, 'inactive'::character varying]::text[])", name='chk_product_pricing_bindings_status'),
        ForeignKeyConstraint(['adapter_id'], ['insurer_api_adapters.id'], name='product_pricing_bindings_adapter_id_fkey'),
        ForeignKeyConstraint(['pricing_schema_id'], ['product_pricing_schemas.id'], name='product_pricing_bindings_pricing_schema_id_fkey'),
        ForeignKeyConstraint(['product_id'], ['products.id'], name='product_pricing_bindings_product_id_fkey'),
        PrimaryKeyConstraint('id', name='product_pricing_bindings_pkey'),
        Index('idx_product_pricing_bindings_product', 'product_id', 'status'),
        {'comment': '产品、试算模板与保险公司适配器的绑定'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, comment='绑定主键')
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属产品')
    pricing_schema_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, comment='试算模板主键')
    adapter_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, comment='适配器主键')
    external_product_code: Mapped[str] = mapped_column(String(120), nullable=False, comment='保险公司外部产品编码')
    api_code: Mapped[str] = mapped_column(String(120), nullable=False, comment='保险公司接口编码')
    field_mapping: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='内部字段到外部字段的映射')
    response_mapping: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='外部响应到统一响应的映射')
    mock_config: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='教学 Mock 试算配置')
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'active'::character varying"), comment='绑定状态')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='最后更新时间')

    adapter: Mapped['InsurerApiAdapters'] = relationship('InsurerApiAdapters', back_populates='product_pricing_bindings')
    pricing_schema: Mapped['ProductPricingSchemas'] = relationship('ProductPricingSchemas', back_populates='product_pricing_bindings')
    product: Mapped['Products'] = relationship('Products', back_populates='product_pricing_bindings')


class RateTableItems(Base):
    __tablename__ = 'rate_table_items'
    __table_args__ = (
        CheckConstraint('(rate_value IS NULL OR rate_value >= 0::numeric) AND (premium IS NULL OR premium >= 0::numeric)', name='chk_rate_table_items_non_negative'),
        CheckConstraint("gender::text = ANY (ARRAY['male'::character varying, 'female'::character varying, 'unisex'::character varying, 'all'::character varying]::text[])", name='chk_rate_table_items_gender'),
        CheckConstraint("social_security::text = ANY (ARRAY['yes'::character varying, 'no'::character varying, 'all'::character varying]::text[])", name='chk_rate_table_items_social_security'),
        CheckConstraint("status::text = ANY (ARRAY['active'::character varying, 'inactive'::character varying]::text[])", name='chk_rate_table_items_status'),
        ForeignKeyConstraint(['product_id'], ['products.id'], name='rate_table_items_product_id_fkey'),
        ForeignKeyConstraint(['rate_file_id'], ['rate_table_files.id'], name='rate_table_items_rate_file_id_fkey'),
        PrimaryKeyConstraint('id', name='rate_table_items_pkey'),
        Index('idx_rate_items_dimensions', 'dimensions', postgresql_using='gin'),
        Index('idx_rate_items_lookup', 'product_id', 'plan_code', 'age_min', 'age_max', 'gender', 'payment_period', 'coverage_period', 'status'),
        {'comment': '费率表中的结构化费率明细'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, comment='费率明细主键')
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属产品')
    plan_code: Mapped[str] = mapped_column(String(80), nullable=False, comment='费率计划编码')
    rate_type: Mapped[str] = mapped_column(String(50), nullable=False, comment='费率计算类型')
    gender: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'all'::character varying"), comment='适用性别')
    occupation_class: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'all'::character varying"), comment='适用职业类别')
    social_security: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'all'::character varying"), comment='社保条件')
    dimensions: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='其他费率维度')
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'active'::character varying"), comment='费率明细状态')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    rate_file_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, comment='来源费率文件')
    age_min: Mapped[Optional[int]] = mapped_column(Integer, comment='适用最小年龄')
    age_max: Mapped[Optional[int]] = mapped_column(Integer, comment='适用最大年龄')
    payment_period: Mapped[Optional[str]] = mapped_column(String(50), comment='缴费期限')
    coverage_period: Mapped[Optional[str]] = mapped_column(String(50), comment='保障期限')
    coverage_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(14, 2), comment='保险金额')
    deductible: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(14, 2), comment='免赔额')
    rate_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(18, 6), comment='费率值')
    premium: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(14, 2), comment='固定保费值')
    source_page: Mapped[Optional[int]] = mapped_column(Integer, comment='来源页码')
    source_table: Mapped[Optional[str]] = mapped_column(String(200), comment='来源表格名称')

    product: Mapped['Products'] = relationship('Products', back_populates='rate_table_items')
    rate_file: Mapped[Optional['RateTableFiles']] = relationship('RateTableFiles', back_populates='rate_table_items')
