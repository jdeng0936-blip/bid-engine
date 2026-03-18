"""
矿井模型
"""
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, AuditMixin


class SysMine(AuditMixin, Base):
    """矿井基础信息表"""
    __tablename__ = "sys_mine"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="矿井名称")
    company: Mapped[str] = mapped_column(String(200), nullable=True, comment="所属公司")
    gas_level: Mapped[str] = mapped_column(String(20), nullable=True, comment="瓦斯等级(低/高/突出)")
    address: Mapped[str] = mapped_column(String(300), nullable=True, comment="矿井地址")
    contact: Mapped[str] = mapped_column(String(50), nullable=True, comment="联系人")
    phone: Mapped[str] = mapped_column(String(20), nullable=True, comment="联系电话")
