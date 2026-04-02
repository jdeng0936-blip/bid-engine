"""
Node 2: RAG 三层检索 — 为每个章节检索相关法规、模板片段、历史案例

复用 HybridRetriever + EmbeddingService，按章节计划分批并发检索。
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from app.services.generation.planner import ChapterPlan

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """单章节的检索结果"""
    chapter_no: str
    std_clauses: list[dict] = field(default_factory=list)
    template_snippets: list[dict] = field(default_factory=list)
    bid_cases: list[dict] = field(default_factory=list)
    table_data: list[dict] = field(default_factory=list)


def _build_query(plan: ChapterPlan) -> str:
    """从章节计划构建检索 query"""
    parts = [plan.title]
    # 取前 3 个关键点拼接，避免 query 过长影响检索质量
    for kp in plan.key_points[:3]:
        parts.append(kp)
    return " ".join(parts)


async def _retrieve_single_chapter(
    session: AsyncSession,
    tenant_id: int,
    plan: ChapterPlan,
    top_k: int,
) -> RetrievalResult:
    """单章节检索：调用 HybridRetriever 获取三层结果"""
    from app.services.retriever import HybridRetriever

    query = _build_query(plan)
    retriever = HybridRetriever(session=session, tenant_id=tenant_id)

    try:
        raw = await retriever.retrieve(
            query=query,
            context={"chapter_no": plan.chapter_no, "title": plan.title},
            top_k=top_k,
        )
    except Exception as e:
        logger.warning("章节 %s 检索失败: %s", plan.chapter_no, e)
        return RetrievalResult(chapter_no=plan.chapter_no)

    # 将 HybridRetriever 的扁平结果拆分为三类
    std_clauses = []
    template_snippets = []
    table_data = []

    for item in raw.get("merged", []):
        item_type = item.get("type", "")
        content = item.get("content", {})
        if item_type == "semantic":
            std_clauses.append(content)
        elif item_type == "snippet":
            template_snippets.append(content)
        elif item_type == "table":
            table_data.append(content)

    # snippet_results 直接作为 bid_cases（历史案例/知识库片段）
    bid_cases = raw.get("snippet_results", [])

    return RetrievalResult(
        chapter_no=plan.chapter_no,
        std_clauses=std_clauses,
        template_snippets=template_snippets,
        bid_cases=bid_cases,
        table_data=table_data,
    )


async def retrieve_context(
    session: AsyncSession,
    tenant_id: int,
    chapter_plans: list[ChapterPlan],
    project_id: int,
    top_k: int = 5,
) -> list[RetrievalResult]:
    """
    RAG 检索节点

    对每个章节计划，并发执行三层检索:
      L1 — pgvector 语义检索（法规 + 知识库）
      L2 — 结构化参数表查询（报价、资质、企业信息）
      L3 — 结果融合 + Re-rank

    Args:
        session: 数据库会话
        tenant_id: 租户 ID（隔离红线）
        chapter_plans: Node 1 输出的章节计划
        project_id: 项目 ID，用于关联查询报价/资质
        top_k: 每层检索返回条数

    Returns:
        每个章节对应的检索结果列表，顺序与 chapter_plans 一致
    """
    tasks = [
        _retrieve_single_chapter(session, tenant_id, plan, top_k)
        for plan in chapter_plans
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    final = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error("章节 %s 检索异常: %s", chapter_plans[i].chapter_no, r)
            final.append(RetrievalResult(chapter_no=chapter_plans[i].chapter_no))
        else:
            final.append(r)

    return final
