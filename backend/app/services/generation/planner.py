"""
Node 1: 大纲规划 — 根据招标要求 + 章节模板输出 JSON 结构化章节计划

输入: 项目 ID、招标要求列表、客户类型
输出: 章节计划列表（编号、标题、关键点、对应评分项）
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.bid_project import BidProject


class ChapterPlan:
    """单章节计划结构"""
    chapter_no: str          # "第一章" / "4.3.1"
    title: str               # 章节标题
    key_points: list[str]    # 必须覆盖的关键点
    mapped_requirements: list[int]  # 对应的 TenderRequirement.id
    estimated_words: int     # 建议字数


async def plan_outline(
    session: AsyncSession,
    project: BidProject,
    customer_type: Optional[str] = None,
) -> list[ChapterPlan]:
    """
    大纲规划节点

    根据招标文件解析出的要求 + 章节模板，生成结构化章节计划。
    调用 LLM 对评分标准做智能映射，确定每章必须覆盖的关键点。

    Args:
        session: 数据库会话
        project: 投标项目（含已解析的 requirements）
        customer_type: 客户类型（学校/医院/政府/企业），影响模板选择

    Returns:
        章节计划列表，按 chapter_no 排序
    """
    raise NotImplementedError("T5 骨架 — 待实现")
