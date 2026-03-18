"""
用户与角色模型
"""
from sqlalchemy import String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, AuditMixin


class SysUser(AuditMixin, Base):
    """系统用户表"""
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="登录账号")
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False, comment="bcrypt哈希密码")
    real_name: Mapped[str] = mapped_column(String(50), nullable=True, comment="真实姓名")
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_role.id"), nullable=True, comment="角色ID")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")

    role = relationship("SysRole", back_populates="users", lazy="selectin")


class SysRole(AuditMixin, Base):
    """系统角色表"""
    __tablename__ = "sys_role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="角色名")
    description: Mapped[str] = mapped_column(String(200), nullable=True, comment="角色描述")

    users = relationship("SysUser", back_populates="role")
