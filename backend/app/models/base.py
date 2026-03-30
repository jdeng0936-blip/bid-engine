"""
SQLAlchemy 基类 — 通用字段 Mixin

规范红线：所有核心表必须包含 created_at, updated_at, created_by, tenant_id
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


class AuditMixin:
    """审计通用字段 Mixin

    所有业务表都必须混入此类，确保 tenant_id 隔离和审计追踪。
    """
    tenant_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, comment="租户ID（企业ID）"
    )
    created_by: Mapped[int] = mapped_column(
        Integer, nullable=True, comment="创建人ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
