"""
Alembic 迁移 — 新增鲜标智投核心表

新增表：enterprise, bid_project, tender_requirement, bid_chapter,
        credential, quotation_sheet, quotation_item, image_asset

Revision ID: b5c6d7e8f9a0
Revises: a2b3c4d5e6f7
Create Date: 2026-03-30 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b5c6d7e8f9a0"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========== enterprise ==========
    op.create_table(
        "enterprise",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False, comment="租户ID"),
        sa.Column("name", sa.String(length=200), nullable=False, comment="企业名称"),
        sa.Column("short_name", sa.String(length=50), nullable=True, comment="企业简称"),
        sa.Column("credit_code", sa.String(length=50), nullable=True, comment="统一社会信用代码"),
        sa.Column("legal_representative", sa.String(length=50), nullable=True, comment="法定代表人"),
        sa.Column("registered_capital", sa.String(length=50), nullable=True, comment="注册资本（万元）"),
        sa.Column("established_date", sa.String(length=20), nullable=True, comment="成立日期"),
        sa.Column("business_scope", sa.Text(), nullable=True, comment="经营范围"),
        sa.Column("food_license_no", sa.String(length=100), nullable=True, comment="食品经营许可证号"),
        sa.Column("food_license_expiry", sa.String(length=20), nullable=True, comment="食品经营许可证到期日"),
        sa.Column("haccp_certified", sa.Boolean(), server_default="false", comment="是否通过HACCP认证"),
        sa.Column("iso22000_certified", sa.Boolean(), server_default="false", comment="是否通过ISO22000认证"),
        sa.Column("sc_certified", sa.Boolean(), server_default="false", comment="是否有SC认证"),
        sa.Column("cold_chain_vehicles", sa.Integer(), server_default="0", comment="冷链车辆数"),
        sa.Column("normal_vehicles", sa.Integer(), server_default="0", comment="常温车辆数"),
        sa.Column("warehouse_area", sa.Float(), nullable=True, comment="仓储面积（㎡）"),
        sa.Column("cold_storage_area", sa.Float(), nullable=True, comment="冷库面积（㎡）"),
        sa.Column("cold_storage_temp", sa.String(length=50), nullable=True, comment="冷库温度范围"),
        sa.Column("address", sa.Text(), nullable=True, comment="公司地址"),
        sa.Column("contact_person", sa.String(length=50), nullable=True, comment="联系人"),
        sa.Column("contact_phone", sa.String(length=20), nullable=True, comment="联系电话"),
        sa.Column("contact_email", sa.String(length=100), nullable=True, comment="邮箱"),
        sa.Column("employee_count", sa.Integer(), nullable=True, comment="员工人数"),
        sa.Column("annual_revenue", sa.String(length=50), nullable=True, comment="年营收（万元）"),
        sa.Column("service_customers", sa.Integer(), nullable=True, comment="服务客户数"),
        sa.Column("description", sa.Text(), nullable=True, comment="企业简介"),
        sa.Column("competitive_advantages", sa.Text(), nullable=True, comment="核心竞争优势"),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="创建人ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_enterprise_tenant_id"), "enterprise", ["tenant_id"], unique=False)

    # ========== bid_project ==========
    op.create_table(
        "bid_project",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False, comment="租户ID"),
        sa.Column("enterprise_id", sa.Integer(), nullable=True, comment="投标企业ID"),
        sa.Column("project_name", sa.String(length=300), nullable=False, comment="招标项目名称"),
        sa.Column("tender_org", sa.String(length=200), nullable=True, comment="招标方名称"),
        sa.Column("tender_contact", sa.String(length=200), nullable=True, comment="招标方联系方式"),
        sa.Column("customer_type", sa.String(length=20), nullable=True, comment="客户类型"),
        sa.Column("tender_type", sa.String(length=20), nullable=True, comment="招标方式"),
        sa.Column("deadline", sa.String(length=30), nullable=True, comment="投标截止时间"),
        sa.Column("bid_opening_time", sa.String(length=30), nullable=True, comment="开标时间"),
        sa.Column("budget_amount", sa.Float(), nullable=True, comment="预算金额（元）"),
        sa.Column("bid_amount", sa.Float(), nullable=True, comment="我方报价金额（元）"),
        sa.Column("delivery_scope", sa.Text(), nullable=True, comment="配送范围描述"),
        sa.Column("delivery_period", sa.String(length=100), nullable=True, comment="配送周期/合同期限"),
        sa.Column("status", sa.String(length=20), server_default="draft", comment="项目状态"),
        sa.Column("tender_doc_path", sa.Text(), nullable=True, comment="招标文件路径"),
        sa.Column("bid_doc_path", sa.Text(), nullable=True, comment="投标文件路径"),
        sa.Column("description", sa.Text(), nullable=True, comment="备注说明"),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="创建人ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["enterprise_id"], ["enterprise.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bid_project_tenant_id"), "bid_project", ["tenant_id"], unique=False)

    # ========== tender_requirement ==========
    op.create_table(
        "tender_requirement",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False, comment="分类"),
        sa.Column("content", sa.Text(), nullable=False, comment="要求内容"),
        sa.Column("is_mandatory", sa.Boolean(), server_default="true", comment="是否为强制要求"),
        sa.Column("score_weight", sa.Float(), nullable=True, comment="评分权重（%）"),
        sa.Column("max_score", sa.Float(), nullable=True, comment="最高分值"),
        sa.Column("sort_order", sa.Integer(), server_default="0", comment="排序号"),
        sa.Column("compliance_status", sa.String(length=20), nullable=True, comment="合规状态"),
        sa.Column("compliance_note", sa.Text(), nullable=True, comment="合规检查备注"),
        sa.Column("tenant_id", sa.Integer(), nullable=False, comment="租户ID"),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="创建人ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["project_id"], ["bid_project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tender_requirement_tenant_id"), "tender_requirement", ["tenant_id"], unique=False)

    # ========== bid_chapter ==========
    op.create_table(
        "bid_chapter",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("chapter_no", sa.String(length=30), nullable=False, comment="章节编号"),
        sa.Column("title", sa.String(length=200), nullable=False, comment="章节标题"),
        sa.Column("content", sa.Text(), nullable=True, comment="章节正文内容"),
        sa.Column("source", sa.String(length=20), server_default="template", comment="内容来源"),
        sa.Column("status", sa.String(length=20), server_default="draft", comment="状态"),
        sa.Column("sort_order", sa.Integer(), server_default="0", comment="排序号"),
        sa.Column("ai_model_used", sa.String(length=50), nullable=True, comment="使用的AI模型"),
        sa.Column("ai_prompt_version", sa.String(length=20), nullable=True, comment="使用的Prompt版本"),
        sa.Column("has_warning", sa.Boolean(), server_default="false", comment="是否有合规警告"),
        sa.Column("tenant_id", sa.Integer(), nullable=False, comment="租户ID"),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="创建人ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["project_id"], ["bid_project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bid_chapter_tenant_id"), "bid_chapter", ["tenant_id"], unique=False)

    # ========== credential ==========
    op.create_table(
        "credential",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False, comment="租户ID"),
        sa.Column("enterprise_id", sa.Integer(), nullable=False),
        sa.Column("cred_type", sa.String(length=50), nullable=False, comment="证书类型"),
        sa.Column("cred_name", sa.String(length=200), nullable=False, comment="证书名称"),
        sa.Column("cred_no", sa.String(length=100), nullable=True, comment="证书编号"),
        sa.Column("issue_date", sa.String(length=20), nullable=True, comment="发证日期"),
        sa.Column("expiry_date", sa.String(length=20), nullable=True, comment="到期日期"),
        sa.Column("is_permanent", sa.Boolean(), server_default="false", comment="是否长期有效"),
        sa.Column("issuing_authority", sa.String(length=200), nullable=True, comment="发证机关"),
        sa.Column("file_path", sa.Text(), nullable=True, comment="扫描件路径"),
        sa.Column("file_name", sa.String(length=200), nullable=True, comment="原始文件名"),
        sa.Column("is_verified", sa.Boolean(), server_default="false", comment="是否已验证"),
        sa.Column("remarks", sa.Text(), nullable=True, comment="备注"),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="创建人ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["enterprise_id"], ["enterprise.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_credential_tenant_id"), "credential", ["tenant_id"], unique=False)

    # ========== quotation_sheet ==========
    op.create_table(
        "quotation_sheet",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", comment="报价版本号"),
        sa.Column("discount_rate", sa.Float(), nullable=True, comment="下浮率"),
        sa.Column("total_amount", sa.Float(), nullable=True, comment="报价总金额（元）"),
        sa.Column("budget_amount", sa.Float(), nullable=True, comment="预算金额（元）"),
        sa.Column("pricing_method", sa.String(length=30), nullable=True, comment="报价方式"),
        sa.Column("remarks", sa.Text(), nullable=True, comment="报价说明"),
        sa.Column("tenant_id", sa.Integer(), nullable=False, comment="租户ID"),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="创建人ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["project_id"], ["bid_project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quotation_sheet_tenant_id"), "quotation_sheet", ["tenant_id"], unique=False)

    # ========== quotation_item ==========
    op.create_table(
        "quotation_item",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sheet_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False, comment="品类"),
        sa.Column("item_name", sa.String(length=100), nullable=False, comment="品名"),
        sa.Column("spec", sa.String(length=100), nullable=True, comment="规格"),
        sa.Column("unit", sa.String(length=20), nullable=True, comment="单位"),
        sa.Column("market_ref_price", sa.Float(), nullable=True, comment="市场参考价（元）"),
        sa.Column("unit_price", sa.Float(), nullable=True, comment="投标单价（元）"),
        sa.Column("quantity", sa.Float(), nullable=True, comment="预计采购量"),
        sa.Column("amount", sa.Float(), nullable=True, comment="小计金额（元）"),
        sa.Column("sort_order", sa.Integer(), server_default="0", comment="排序号"),
        sa.Column("tenant_id", sa.Integer(), nullable=False, comment="租户ID"),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="创建人ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["sheet_id"], ["quotation_sheet.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quotation_item_tenant_id"), "quotation_item", ["tenant_id"], unique=False)

    # ========== image_asset ==========
    op.create_table(
        "image_asset",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False, comment="租户ID"),
        sa.Column("enterprise_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False, comment="图片分类"),
        sa.Column("title", sa.String(length=200), nullable=False, comment="图片标题"),
        sa.Column("description", sa.Text(), nullable=True, comment="图片说明文字"),
        sa.Column("file_path", sa.Text(), nullable=False, comment="图片存储路径"),
        sa.Column("file_name", sa.String(length=200), nullable=True, comment="原始文件名"),
        sa.Column("file_size", sa.Integer(), nullable=True, comment="文件大小（字节）"),
        sa.Column("mime_type", sa.String(length=50), nullable=True, comment="MIME类型"),
        sa.Column("width", sa.Integer(), nullable=True, comment="图片宽度（像素）"),
        sa.Column("height", sa.Integer(), nullable=True, comment="图片高度（像素）"),
        sa.Column("tags", sa.String(length=500), nullable=True, comment="标签（逗号分隔）"),
        sa.Column("suggested_chapter", sa.String(length=100), nullable=True, comment="建议放置的章节"),
        sa.Column("is_default", sa.Boolean(), server_default="false", comment="是否为该分类的默认图片"),
        sa.Column("sort_order", sa.Integer(), server_default="0", comment="排序号"),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="创建人ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["enterprise_id"], ["enterprise.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_image_asset_tenant_id"), "image_asset", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_table("image_asset")
    op.drop_table("quotation_item")
    op.drop_table("quotation_sheet")
    op.drop_table("credential")
    op.drop_table("bid_chapter")
    op.drop_table("tender_requirement")
    op.drop_table("bid_project")
    op.drop_table("enterprise")
