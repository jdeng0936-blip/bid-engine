"""
Node 3: 草稿生成 — 结合企业画像 + RAG 结果调用 LLM 生成章节初稿

架构红线: 报价数值禁止用 LLM 输出，必须从 QuotationSheet 计算引擎注入。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.bid_project import BidProject

from app.services.generation.planner import ChapterPlan
from app.services.generation.retriever import RetrievalResult


class DraftChapter:
    """单章节草稿"""
    chapter_no: str
    title: str
    content: str              # Markdown 格式正文
    sources_cited: list[str]  # 引用的法规/案例来源
    word_count: int


async def generate_draft(
    session: AsyncSession,
    project: BidProject,
    chapter_plans: list[ChapterPlan],
    retrieval_results: list[RetrievalResult],
    enterprise_info: Optional[str] = None,
) -> list[DraftChapter]:
    """
    草稿生成节点

    逐章调用 LLM，将章节计划 + RAG 检索结果 + 企业画像融合为投标文档初稿。
    报价相关章节从 QuotationSheet 注入精确数值，不依赖 LLM 生成。

    Args:
        session: 数据库会话
        project: 投标项目
        chapter_plans: Node 1 输出的章节计划
        retrieval_results: Node 2 输出的检索结果
        enterprise_info: 预构建的企业信息文本块（含资质编号）

    Returns:
        各章节草稿列表
    """
    raise NotImplementedError("T5 骨架 — 待实现")
