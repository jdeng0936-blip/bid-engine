"""
Node 6: 评分点覆盖校验 — 检查每个评分标准是否在章节中被充分响应

输出覆盖率矩阵和未覆盖项清单，供人工审阅或触发回写。
"""
from typing import Optional

from app.services.generation.polish_pipeline import PolishResult


class ScoringCoverage:
    """单个评分项的覆盖情况"""
    requirement_id: int
    requirement_text: str
    max_score: Optional[float]
    covered_in: list[str]       # 覆盖该评分项的章节编号列表
    coverage_score: float       # 0.0~1.0 覆盖度评分
    gap_note: Optional[str]     # 未充分覆盖时的说明


class ReviewReport:
    """评分覆盖校验报告"""
    overall_coverage: float          # 整体覆盖率 0.0~1.0
    scoring_items: list[ScoringCoverage]
    uncovered_items: list[ScoringCoverage]  # coverage_score < 阈值的项
    chapters: list[PolishResult]     # 透传润色后的章节


async def review_scoring_coverage(
    chapters: list[PolishResult],
    scoring_requirements: list[dict],
    threshold: float = 0.6,
) -> ReviewReport:
    """
    评分点覆盖校验节点

    将评分标准逐项与章节内容做语义匹配，计算覆盖度。
    低于阈值的评分项标记为 uncovered，附带补充建议。

    Args:
        chapters: Node 5 输出的润色后章节
        scoring_requirements: 评分类招标要求（category="scoring"）
        threshold: 覆盖度阈值，低于此值视为未覆盖

    Returns:
        覆盖校验报告，含整体覆盖率和逐项明细
    """
    raise NotImplementedError("T5 骨架 — 待实现")
