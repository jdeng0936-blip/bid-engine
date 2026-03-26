"""
AI 对话会话 + 消息历史持久化模型

功能说明：
  1. ChatSession — 对话会话（一次完整的多轮对话）
  2. ChatMessage — 会话内的每条消息（user/assistant/tool角色）

设计原则：
  - 每个会话绑定 tenant_id + user_id，支持多租户隔离
  - 消息按 created_at 时序存储，查询时按序还原历史
  - 支持关联项目（project_id），便于在项目上下文中持续对话
"""
from sqlalchemy import String, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, AuditMixin


class ChatSession(AuditMixin, Base):
    """AI 对话会话"""
    __tablename__ = "chat_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, comment="用户ID"
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=True, comment="会话标题（自动取首条消息前50字）"
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id", ondelete="SET NULL"),
        nullable=True, index=True, comment="关联项目ID（可选）"
    )
    industry_type: Mapped[str] = mapped_column(
        String(50), default="coal_excavation", comment="行业类型"
    )
    is_archived: Mapped[bool] = mapped_column(
        Integer, default=0, comment="是否归档(0=活跃/1=归档)"
    )

    # 关联消息
    messages = relationship(
        "ChatMessageRecord", back_populates="session",
        lazy="selectin", cascade="all, delete-orphan",
        order_by="ChatMessageRecord.created_at",
    )


class ChatMessageRecord(AuditMixin, Base):
    """对话消息记录"""
    __tablename__ = "chat_message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat_session.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="所属会话ID"
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="消息角色(user/assistant/tool/system)"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="消息内容"
    )
    # 工具调用相关（assistant 消息可能包含 tool_calls）
    tool_calls: Mapped[dict] = mapped_column(
        JSON, nullable=True, comment="工具调用信息(JSON)"
    )
    tool_call_id: Mapped[str] = mapped_column(
        String(100), nullable=True, comment="工具调用ID（tool角色消息）"
    )
    tool_name: Mapped[str] = mapped_column(
        String(50), nullable=True, comment="工具名称（tool角色消息）"
    )

    # 关联
    session = relationship("ChatSession", back_populates="messages")
