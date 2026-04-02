"""
Node 2: RAG 三层检索 — 为每个章节检索相关法规、模板片段、历史案例

复用 embedding_service + HybridRetriever，按章节计划分批检索。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.services.generation.planner import ChapterPlan


class RetrievalResult:
    """单章节的检索结果"""
    chapter_no: str
    std_clauses: list[dict]      # 法规标准条款
    template_snippets: list[dict]  # 知识库模板片段
    bid_cases: list[dict]        # 历史中标案例
    table_data: list[dict]       # 结构化查表结果（报价/资质等）


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
        每个章节对应的检索结果列表
    """
    raise NotImplementedError("T5 骨架 — 待实现")
