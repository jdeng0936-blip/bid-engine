"""
设备材料目录 + 项目设备材料清单数据模型

功能说明：
  1. EquipmentCatalog — 设备目录（掘进/支护/运输/通风/排水/电气设备）
  2. MaterialCatalog — 材料目录（锚杆/锚索/药卷/金属网/W钢带/托盘/喷混等）
  3. ProjectEquipmentList — 项目推荐设备清单
  4. ProjectMaterialBom — 项目材料工程量清单（按循环/月/总量分级）
"""
from sqlalchemy import String, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, AuditMixin


class EquipmentCatalog(AuditMixin, Base):
    """设备目录 — 存储所有可选设备的基础信息"""
    __tablename__ = "equipment_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="设备名称")
    category: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True,
        comment="设备类别(掘进设备/支护设备/运输设备/通风设备/排水设备/电气设备/其他)"
    )
    model_spec: Mapped[str] = mapped_column(String(100), nullable=True, comment="型号规格")
    manufacturer: Mapped[str] = mapped_column(String(100), nullable=True, comment="生产厂家")
    power_kw: Mapped[float] = mapped_column(Float, nullable=True, comment="额定功率(kW)")
    weight_t: Mapped[float] = mapped_column(Float, nullable=True, comment="设备重量(t)")
    tech_params: Mapped[dict] = mapped_column(JSON, nullable=True, comment="主要技术参数(JSON)")
    applicable_conditions: Mapped[str] = mapped_column(
        Text, nullable=True,
        comment="适用条件描述(围岩级别/掘进方式/断面范围等)"
    )
    # 匹配规则：用于自动推荐时的条件筛选
    match_dig_methods: Mapped[str] = mapped_column(
        String(100), nullable=True,
        comment="适用掘进方式(逗号分隔，如: 综掘,炮掘)"
    )
    match_excavation_types: Mapped[str] = mapped_column(
        String(100), nullable=True,
        comment="适用掘进类型(逗号分隔，如: 煤巷,半煤岩巷)"
    )
    match_min_section_area: Mapped[float] = mapped_column(
        Float, nullable=True, comment="适用最小断面面积(m²)"
    )
    match_max_section_area: Mapped[float] = mapped_column(
        Float, nullable=True, comment="适用最大断面面积(m²)"
    )
    is_active: Mapped[bool] = mapped_column(
        Integer, default=1, comment="是否启用(1=启用/0=停用)"
    )


class MaterialCatalog(AuditMixin, Base):
    """材料目录 — 存储所有可选支护及辅助材料"""
    __tablename__ = "material_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="材料名称")
    category: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True,
        comment="材料类别(锚杆/锚索/树脂药卷/金属网/W钢带/托盘/喷射混凝土/其他)"
    )
    model_spec: Mapped[str] = mapped_column(String(100), nullable=True, comment="规格型号")
    unit: Mapped[str] = mapped_column(String(10), nullable=False, default="根", comment="计量单位")
    # 单次循环消耗量基准（用于工程量计算）
    consumption_per_cycle: Mapped[float] = mapped_column(
        Float, nullable=True,
        comment="单循环消耗量（基准值，实际根据断面调整）"
    )
    # 匹配规则
    match_support_types: Mapped[str] = mapped_column(
        String(100), nullable=True,
        comment="适用支护方式(逗号分隔，如: 锚网支护,锚网索支护)"
    )
    match_rock_classes: Mapped[str] = mapped_column(
        String(50), nullable=True,
        comment="适用围岩级别(逗号分隔，如: III,IV,V)"
    )
    tech_params: Mapped[dict] = mapped_column(JSON, nullable=True, comment="技术参数(JSON)")
    is_active: Mapped[bool] = mapped_column(
        Integer, default=1, comment="是否启用"
    )


class ProjectEquipmentList(AuditMixin, Base):
    """项目设备清单 — 根据项目参数自动匹配推荐的设备列表"""
    __tablename__ = "project_equipment_list"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="关联项目ID"
    )
    equipment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("equipment_catalog.id"),
        nullable=True, comment="关联设备目录ID（手动添加时可为空）"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="设备名称")
    category: Mapped[str] = mapped_column(String(30), nullable=False, comment="设备类别")
    model_spec: Mapped[str] = mapped_column(String(100), nullable=True, comment="型号规格")
    quantity: Mapped[int] = mapped_column(Integer, default=1, comment="数量(台/套)")
    power_kw: Mapped[float] = mapped_column(Float, nullable=True, comment="额定功率(kW)")
    tech_params_summary: Mapped[str] = mapped_column(
        Text, nullable=True, comment="主要技术参数摘要"
    )
    match_source: Mapped[str] = mapped_column(
        String(20), default="auto", comment="匹配来源(auto=自动推荐/manual=手动添加)"
    )

    # 关联
    equipment = relationship("EquipmentCatalog", lazy="selectin")


class ProjectMaterialBom(AuditMixin, Base):
    """项目材料工程量清单 — 按循环/月/总量分级的材料 BOM"""
    __tablename__ = "project_material_bom"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="关联项目ID"
    )
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("material_catalog.id"),
        nullable=True, comment="关联材料目录ID"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="材料名称")
    category: Mapped[str] = mapped_column(String(30), nullable=False, comment="材料类别")
    model_spec: Mapped[str] = mapped_column(String(100), nullable=True, comment="规格型号")
    unit: Mapped[str] = mapped_column(String(10), nullable=False, comment="计量单位")
    # 分级工程量
    qty_per_cycle: Mapped[float] = mapped_column(
        Float, nullable=True, comment="单循环用量"
    )
    qty_per_month: Mapped[float] = mapped_column(
        Float, nullable=True, comment="月用量"
    )
    qty_total: Mapped[float] = mapped_column(
        Float, nullable=True, comment="工程总量"
    )
    # 计算依据
    calc_basis: Mapped[str] = mapped_column(
        Text, nullable=True, comment="计算依据说明"
    )
    match_source: Mapped[str] = mapped_column(
        String(20), default="auto", comment="匹配来源(auto/manual)"
    )

    # 关联
    material = relationship("MaterialCatalog", lazy="selectin")
