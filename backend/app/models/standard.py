"""
知识库模型 — 法规文档 / 条款 / 历史中标案例

StdDocument: 规范文档（食品安全法/冷链标准/采购规范等）
StdClause: 条款（结构化拆解 + pgvector 语义检索）
BidCase: 历史中标案例（替代原 EngCase 煤矿案例）
"""
from sqlalchemy import String, Integer, Text, Boolean, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.models.base import Base, AuditMixin


class StdDocument(AuditMixin, Base):
    """法规/标准文档"""
    __tablename__ = "std_document"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="文档名称")
    doc_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="文档类型: food_safety_law/cold_chain_standard/procurement_regulation/haccp/bid_template"
    )
    version: Mapped[str] = mapped_column(String(30), nullable=True, comment="版本号")
    publish_date: Mapped[str] = mapped_column(Date, nullable=True, comment="发布日期")
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否现行有效")
    file_url: Mapped[str] = mapped_column(String(500), nullable=True, comment="原文件存储地址")

    clauses = relationship("StdClause", back_populates="document", lazy="selectin")


class StdClause(Base):
    """条款（结构化拆解 + 向量检索）"""
    __tablename__ = "std_clause"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("std_document.id"), nullable=False)
    parent_id: Mapped[int] = mapped_column(Integer, nullable=True, comment="父条款ID（树形结构）")
    clause_no: Mapped[str] = mapped_column(String(30), nullable=True, comment="条款编号")
    title: Mapped[str] = mapped_column(String(200), nullable=True, comment="条款标题")
    content: Mapped[str] = mapped_column(Text, nullable=True, comment="条款正文")
    level: Mapped[int] = mapped_column(Integer, default=0, comment="层级深度")
    # pgvector 向量列 — 用于语义检索
    embedding = mapped_column(Vector(1536), nullable=True, comment="文本嵌入向量(1536维)")

    document = relationship("StdDocument", back_populates="clauses")


class BidCase(AuditMixin, Base):
    """历史中标案例（替代原 EngCase）"""
    __tablename__ = "bid_case"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="案例名称")
    customer_type: Mapped[str] = mapped_column(
        String(20), nullable=True, comment="客户类型: school/hospital/government/enterprise"
    )
    buyer_name: Mapped[str] = mapped_column(String(200), nullable=True, comment="采购方名称")
    bid_amount: Mapped[str] = mapped_column(String(50), nullable=True, comment="中标金额")
    discount_rate: Mapped[str] = mapped_column(String(20), nullable=True, comment="下浮率")
    win_date: Mapped[str] = mapped_column(String(20), nullable=True, comment="中标日期")
    summary: Mapped[str] = mapped_column(Text, nullable=True, comment="案例摘要/技术亮点")
    file_url: Mapped[str] = mapped_column(String(500), nullable=True, comment="案例文件存储地址")
    # 向量列 — 用于相似案例检索
    embedding = mapped_column(Vector(1536), nullable=True, comment="摘要嵌入向量(1536维)")
