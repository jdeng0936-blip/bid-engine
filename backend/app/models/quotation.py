"""
报价表模型 — 六大品类食材报价

QuotationSheet: 报价表主表（一个项目支持多版本报价）
QuotationItem: 报价明细行（按品类分类）

品类分类：蔬菜(vegetable) / 肉类(meat) / 水产(seafood)
         蛋禽(egg_poultry) / 干货(dry_goods) / 调料(condiment)
"""
import enum

from sqlalchemy import String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, AuditMixin


class FoodCategory(str, enum.Enum):
    """食材品类"""
    VEGETABLE = "vegetable"         # 蔬菜类
    MEAT = "meat"                   # 肉类
    SEAFOOD = "seafood"             # 水产类
    EGG_POULTRY = "egg_poultry"     # 蛋禽类
    DRY_GOODS = "dry_goods"         # 干货类
    CONDIMENT = "condiment"         # 调料类


class QuotationSheet(AuditMixin, Base):
    """报价表主表"""
    __tablename__ = "quotation_sheet"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bid_project.id", ondelete="CASCADE"), nullable=False
    )

    # --- 报价信息 ---
    version: Mapped[int] = mapped_column(Integer, default=1, comment="报价版本号")
    discount_rate: Mapped[float] = mapped_column(
        Float, nullable=True, comment="下浮率（如0.08代表下浮8%）"
    )
    total_amount: Mapped[float] = mapped_column(
        Float, nullable=True, comment="报价总金额（元）"
    )
    budget_amount: Mapped[float] = mapped_column(
        Float, nullable=True, comment="预算金额（元），从招标文件提取"
    )

    # --- 附加信息 ---
    pricing_method: Mapped[str] = mapped_column(
        String(30), nullable=True,
        comment="报价方式: fixed_price/discount_rate/comprehensive"
    )
    remarks: Mapped[str] = mapped_column(Text, nullable=True, comment="报价说明/备注")

    # --- 关联 ---
    project = relationship("BidProject", back_populates="quotation_sheets")
    items = relationship(
        "QuotationItem", back_populates="sheet", lazy="selectin",
        cascade="all, delete-orphan", passive_deletes=True,
        order_by="QuotationItem.sort_order",
    )


class QuotationItem(AuditMixin, Base):
    """报价明细行"""
    __tablename__ = "quotation_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sheet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quotation_sheet.id", ondelete="CASCADE"), nullable=False
    )

    # --- 品目信息 ---
    category: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="品类: vegetable/meat/seafood/egg_poultry/dry_goods/condiment"
    )
    item_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="品名（如: 小白菜、五花肉）")
    spec: Mapped[str] = mapped_column(String(100), nullable=True, comment="规格（如: 一级、精品）")
    unit: Mapped[str] = mapped_column(String(20), nullable=True, comment="单位（kg/斤/箱/个）")

    # --- 价格 ---
    market_ref_price: Mapped[float] = mapped_column(
        Float, nullable=True, comment="市场参考价（元）"
    )
    unit_price: Mapped[float] = mapped_column(
        Float, nullable=True, comment="投标单价（元） = 参考价 × (1 - 下浮率)"
    )
    quantity: Mapped[float] = mapped_column(
        Float, nullable=True, comment="预计采购量"
    )
    amount: Mapped[float] = mapped_column(
        Float, nullable=True, comment="小计金额（元） = 单价 × 数量"
    )

    # --- 排序 ---
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")

    # --- 关联 ---
    sheet = relationship("QuotationSheet", back_populates="items")
