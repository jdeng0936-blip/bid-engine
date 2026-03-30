"""
文档模型 — 生成记录 / Word 模板 / 章节片段

GeneratedDoc: 已生成的投标文件记录（关联 bid_project）
DocTemplate:  投标文件 Word 模板（按客户类型分类）
ChapterSnippet: 章节内容片段 / 通用模板片段（含向量检索）
"""
from sqlalchemy import String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.models.base import Base, AuditMixin


class GeneratedDoc(AuditMixin, Base):
    """生成的投标文件记录"""
    __tablename__ = "generated_doc"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bid_project.id", ondelete="CASCADE"), nullable=False
    )
    file_url: Mapped[str] = mapped_column(String(500), nullable=False, comment="文档存储地址")
    file_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="文件名")
    file_size_mb: Mapped[float] = mapped_column(Float, nullable=True, comment="文件大小(MB)")
    doc_format: Mapped[str] = mapped_column(
        String(10), default="docx", comment="文件格式: docx/pdf"
    )
    version: Mapped[int] = mapped_column(Integer, default=1, comment="文档版本号")


class DocTemplate(AuditMixin, Base):
    """投标文件 Word 模板"""
    __tablename__ = "doc_template"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="模板名称")
    description: Mapped[str] = mapped_column(Text, nullable=True, comment="模板描述")
    customer_type: Mapped[str] = mapped_column(
        String(20), nullable=True,
        comment="适用客户类型: school/hospital/government/enterprise/canteen（空=通用）"
    )
    file_url: Mapped[str] = mapped_column(String(500), nullable=False, comment="模板文件存储地址")
    is_default: Mapped[bool] = mapped_column(Integer, default=False, comment="是否默认模板")


class ChapterSnippet(AuditMixin, Base):
    """章节内容片段 / 通用模板片段"""
    __tablename__ = "chapter_snippet"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chapter_no: Mapped[str] = mapped_column(String(20), nullable=False, comment="章节编号")
    chapter_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="章节名称")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="内容片段(Jinja2 模板)")
    customer_type: Mapped[str] = mapped_column(
        String(20), nullable=True,
        comment="适用客户类型: school/hospital/government/enterprise（空=通用）"
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序权重")
    # pgvector 向量列 — 用于语义检索
    embedding = mapped_column(Vector(1536), nullable=True, comment="文本嵌入向量(1536维)")
