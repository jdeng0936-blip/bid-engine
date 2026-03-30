"""
资质证书库模型 — 企业证照管理

功能：
  - 证照基本信息（类型/编号/有效期/发证机关）
  - 到期预警（提前N天提醒）
  - 投标必需资质 vs 企业已有资质 匹配检查
  - 扫描件存储路径
"""
import enum

from sqlalchemy import String, Integer, Text, Date, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, AuditMixin


class CredentialType(str, enum.Enum):
    """资质证书类型"""
    FOOD_LICENSE = "food_license"                 # 食品经营许可证
    BUSINESS_LICENSE = "business_license"          # 营业执照
    HACCP = "haccp"                                # HACCP认证
    ISO22000 = "iso22000"                          # ISO22000认证
    SC = "sc"                                      # SC认证（食品生产许可）
    ANIMAL_QUARANTINE = "animal_quarantine"         # 动物防疫合格证
    COLD_CHAIN_TRANSPORT = "cold_chain_transport"   # 冷链运输资质
    HEALTH_CERTIFICATE = "health_certificate"       # 从业人员健康证
    LIABILITY_INSURANCE = "liability_insurance"     # 公众责任险
    QUALITY_INSPECTION = "quality_inspection"       # 质量检验报告
    ORGANIC_CERT = "organic_cert"                   # 有机认证
    GREEN_FOOD = "green_food"                       # 绿色食品认证
    BUSINESS_PERFORMANCE = "performance"            # 业绩证明
    AWARD_HONOR = "award"                           # 荣誉证书
    OTHER = "other"                                 # 其他


class Credential(AuditMixin, Base):
    """企业资质证书"""
    __tablename__ = "credential"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="租户ID")
    enterprise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("enterprise.id", ondelete="CASCADE"), nullable=False
    )

    # --- 证书基本信息 ---
    cred_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="证书类型（见 CredentialType 枚举）"
    )
    cred_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="证书名称")
    cred_no: Mapped[str] = mapped_column(String(100), nullable=True, comment="证书编号")

    # --- 有效期 ---
    issue_date: Mapped[str] = mapped_column(String(20), nullable=True, comment="发证日期")
    expiry_date: Mapped[str] = mapped_column(String(20), nullable=True, comment="到期日期")
    is_permanent: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否长期有效")

    # --- 发证机关 ---
    issuing_authority: Mapped[str] = mapped_column(String(200), nullable=True, comment="发证机关")

    # --- 文件存储 ---
    file_path: Mapped[str] = mapped_column(Text, nullable=True, comment="扫描件/电子件路径")
    file_name: Mapped[str] = mapped_column(String(200), nullable=True, comment="原始文件名")

    # --- 状态 ---
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已验证")
    remarks: Mapped[str] = mapped_column(Text, nullable=True, comment="备注")

    # --- 关联 ---
    enterprise = relationship("Enterprise", back_populates="credentials")
