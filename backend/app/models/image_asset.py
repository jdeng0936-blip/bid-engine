"""
图片资源库模型 — 投标文件图片管理

关键需求（用户反馈）：投标文件需要引用大量图片，必须建立图片库。

图片类型包括：
  - 冷链车辆照片（车牌/GPS设备/温控仪表/车厢内部）
  - 仓库/冷库照片（温区标识/温控设备/储存环境）
  - 检测设备照片（农残速测仪/食品快检设备）
  - 配送流程图/组织架构图
  - 食材样品照片
  - 公司环境照片（外景/办公区/培训场景）
  - 留样柜照片
  - 检验检测报告扫描件
  - 荣誉证书/奖项照片
  - 其他（自定义）

使用方式：
  1. 企业上传图片到图片库，添加类型标签
  2. AI生成章节时，通过 [[IMG:图片ID:说明文字]] 标记引用
  3. 文档装配阶段，将标记替换为实际图片插入到Word中
"""
import enum

from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, AuditMixin


class ImageCategory(str, enum.Enum):
    """图片分类"""
    COLD_CHAIN_VEHICLE = "cold_chain_vehicle"       # 冷链车辆
    WAREHOUSE = "warehouse"                          # 仓库/冷库
    TESTING_EQUIPMENT = "testing_equipment"           # 检测设备
    FOOD_SAMPLE = "food_sample"                      # 食材样品
    PROCESS_FLOW = "process_flow"                    # 流程图/架构图
    COMPANY_ENVIRONMENT = "company_environment"       # 公司环境
    SAMPLE_RETENTION = "sample_retention"             # 留样柜
    INSPECTION_REPORT = "inspection_report"           # 检验报告
    CERTIFICATE = "certificate"                       # 证书/奖项
    DELIVERY_SCENE = "delivery_scene"                 # 配送现场
    TRAINING = "training"                             # 培训场景
    CANTEEN = "canteen"                               # 食堂/餐厅
    TRACEABILITY = "traceability"                     # 追溯系统截图
    OTHER = "other"                                   # 其他


class ImageAsset(AuditMixin, Base):
    """图片资源"""
    __tablename__ = "image_asset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="租户ID")
    enterprise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("enterprise.id", ondelete="CASCADE"), nullable=False
    )

    # --- 图片信息 ---
    category: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="图片分类（见 ImageCategory 枚举）"
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="图片标题（如: 冷链配送车-京A12345）")
    description: Mapped[str] = mapped_column(Text, nullable=True, comment="图片说明文字（插入文档时的图注）")

    # --- 文件信息 ---
    file_path: Mapped[str] = mapped_column(Text, nullable=False, comment="图片存储路径")
    file_name: Mapped[str] = mapped_column(String(200), nullable=True, comment="原始文件名")
    file_size: Mapped[int] = mapped_column(Integer, nullable=True, comment="文件大小（字节）")
    mime_type: Mapped[str] = mapped_column(String(50), nullable=True, comment="MIME类型（image/jpeg等）")

    # --- 图片参数 ---
    width: Mapped[int] = mapped_column(Integer, nullable=True, comment="图片宽度（像素）")
    height: Mapped[int] = mapped_column(Integer, nullable=True, comment="图片高度（像素）")

    # --- 标签（多个标签用逗号分隔） ---
    tags: Mapped[str] = mapped_column(String(500), nullable=True, comment="标签（逗号分隔，如: 冷链,车辆,GPS）")

    # --- 在投标文件中的使用建议 ---
    suggested_chapter: Mapped[str] = mapped_column(
        String(100), nullable=True,
        comment="建议放置的章节（如: 4.4.2 冷链运输方案）"
    )
    is_default: Mapped[bool] = mapped_column(
        default=False, comment="是否为该分类的默认图片（生成时优先使用）"
    )

    # --- 排序 ---
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")

    # --- 关联 ---
    enterprise = relationship("Enterprise", back_populates="images")
