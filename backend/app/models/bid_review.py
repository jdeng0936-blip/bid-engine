"""
投标复盘模型 — 记录项目结果、竞争对手、反馈和复盘
"""
from sqlalchemy import String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin


class BidProjectReview(AuditMixin, Base):
    """项目复盘记录"""
    __tablename__ = "bid_project_review"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("bid_project.id", ondelete="CASCADE"), nullable=False, unique=True, comment="关联投标项目")
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="租户ID")

    # 结果
    result: Mapped[str] = mapped_column(String(20), nullable=False, comment="投标结果: won/lost/disqualified/abandoned")
    result_reason: Mapped[str] = mapped_column(Text, nullable=True, comment="结果原因")
    our_bid_price: Mapped[float] = mapped_column(Float, nullable=True, comment="我方报价（万元）")
    winning_price: Mapped[float] = mapped_column(Float, nullable=True, comment="中标价格（万元）")

    # 反馈
    official_feedback: Mapped[str] = mapped_column(Text, nullable=True, comment="采购方评标意见/扣分项")
    personal_summary: Mapped[str] = mapped_column(Text, nullable=True, comment="业务人员复盘总结")
    lessons_learned: Mapped[str] = mapped_column(Text, nullable=True, comment="经验教训")
    improvement_actions: Mapped[str] = mapped_column(Text, nullable=True, comment="改进措施")

    # 关联
    competitors = relationship("BidCompetitor", back_populates="review", lazy="selectin", cascade="all, delete-orphan")


class BidCompetitor(AuditMixin, Base):
    """竞争对手信息"""
    __tablename__ = "bid_competitor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(Integer, ForeignKey("bid_project_review.id", ondelete="CASCADE"), nullable=False)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="租户ID")

    competitor_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="竞争企业名称")
    competitor_price: Mapped[float] = mapped_column(Float, nullable=True, comment="对手报价（万元）")
    competitor_result: Mapped[str] = mapped_column(String(20), nullable=True, comment="对手结果: won/lost/disqualified")
    competitor_strengths: Mapped[str] = mapped_column(Text, nullable=True, comment="对手优势分析")
    notes: Mapped[str] = mapped_column(Text, nullable=True, comment="备注")

    review = relationship("BidProjectReview", back_populates="competitors")
