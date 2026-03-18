"""
标准库模型 — 规范文档 / 条款 / 工程案例
"""
from sqlalchemy import String, Integer, Text, Boolean, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.models.base import Base, AuditMixin


class StdDocument(AuditMixin, Base):
    """规范文档"""
    __tablename__ = "std_document"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="规范名称")
    doc_type: Mapped[str] = mapped_column(String(30), nullable=False, comment="文档类型(法律法规/技术规范/集团标准/安全规程)")
    version: Mapped[str] = mapped_column(String(30), nullable=True, comment="版本号")
    publish_date: Mapped[str] = mapped_column(Date, nullable=True, comment="发布日期")
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否现行有效")
    file_url: Mapped[str] = mapped_column(String(500), nullable=True, comment="原文件 OSS 地址")

    clauses = relationship("StdClause", back_populates="document", lazy="selectin")


class StdClause(Base):
    """规范条款（结构化拆解 + 向量检索）"""
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


class EngCase(AuditMixin, Base):
    """工程案例"""
    __tablename__ = "eng_case"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="案例名称")
    mine_name: Mapped[str] = mapped_column(String(100), nullable=True, comment="矿井名称")
    excavation_type: Mapped[str] = mapped_column(String(20), nullable=True, comment="掘进类型")
    rock_class: Mapped[str] = mapped_column(String(10), nullable=True, comment="围岩级别")
    summary: Mapped[str] = mapped_column(Text, nullable=True, comment="案例摘要")
    file_url: Mapped[str] = mapped_column(String(500), nullable=True, comment="案例文件 OSS 地址")
