"""
企业信息模型 — 投标主体（替代原 sys_mine 矿井模型）

每个投标企业拥有：
  - 基本工商信息（营业执照信息）
  - 食品行业专属字段（食品经营许可证、冷链资产、HACCP认证等）
  - 多租户隔离（tenant_id）
"""
from sqlalchemy import String, Integer, Float, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, AuditMixin


class Enterprise(AuditMixin, Base):
    """投标企业"""
    __tablename__ = "enterprise"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="租户ID")

    # --- 工商基本信息 ---
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="企业名称")
    short_name: Mapped[str] = mapped_column(String(50), nullable=True, comment="企业简称")
    credit_code: Mapped[str] = mapped_column(String(50), nullable=True, comment="统一社会信用代码")
    legal_representative: Mapped[str] = mapped_column(String(50), nullable=True, comment="法定代表人")
    registered_capital: Mapped[str] = mapped_column(String(50), nullable=True, comment="注册资本（万元）")
    established_date: Mapped[str] = mapped_column(String(20), nullable=True, comment="成立日期")
    business_scope: Mapped[str] = mapped_column(Text, nullable=True, comment="经营范围")

    # --- 食品行业专属 ---
    food_license_no: Mapped[str] = mapped_column(String(100), nullable=True, comment="食品经营许可证号")
    food_license_expiry: Mapped[str] = mapped_column(String(20), nullable=True, comment="食品经营许可证到期日")
    haccp_certified: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否通过HACCP认证")
    iso22000_certified: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否通过ISO22000认证")
    sc_certified: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否有SC认证")

    # --- 冷链资产 ---
    cold_chain_vehicles: Mapped[int] = mapped_column(Integer, default=0, comment="冷链车辆数")
    normal_vehicles: Mapped[int] = mapped_column(Integer, default=0, comment="常温车辆数")
    warehouse_area: Mapped[float] = mapped_column(Float, nullable=True, comment="仓储面积（㎡）")
    cold_storage_area: Mapped[float] = mapped_column(Float, nullable=True, comment="冷库面积（㎡）")
    cold_storage_temp: Mapped[str] = mapped_column(String(50), nullable=True, comment="冷库温度范围（如: -18℃~4℃）")

    # --- 联系信息 ---
    address: Mapped[str] = mapped_column(Text, nullable=True, comment="公司地址")
    contact_person: Mapped[str] = mapped_column(String(50), nullable=True, comment="联系人")
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=True, comment="联系电话")
    contact_email: Mapped[str] = mapped_column(String(100), nullable=True, comment="邮箱")

    # --- 经营数据 ---
    employee_count: Mapped[int] = mapped_column(Integer, nullable=True, comment="员工人数")
    annual_revenue: Mapped[str] = mapped_column(String(50), nullable=True, comment="年营收（万元）")
    service_customers: Mapped[int] = mapped_column(Integer, nullable=True, comment="服务客户数")

    # --- 简介 ---
    description: Mapped[str] = mapped_column(Text, nullable=True, comment="企业简介（用于投标文件）")
    competitive_advantages: Mapped[str] = mapped_column(Text, nullable=True, comment="核心竞争优势（用于技术方案）")

    # --- 关联 ---
    credentials = relationship("Credential", back_populates="enterprise", lazy="selectin",
                               cascade="all, delete-orphan")
    images = relationship("ImageAsset", back_populates="enterprise", lazy="selectin",
                          cascade="all, delete-orphan")
