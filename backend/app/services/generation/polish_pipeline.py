"""
Node 5: 多轮润色 — 术语统一 / 文风适配 / 逻辑连贯性优化

支持配置润色轮次（默认 2 轮），每轮聚焦不同维度。
"""
from typing import Optional

from app.services.generation.writer import DraftChapter


class PolishConfig:
    """润色配置"""
    max_rounds: int = 2                   # 最大润色轮次
    focus_dimensions: list[str] = None    # 聚焦维度: terminology/style/logic
    customer_type: Optional[str] = None   # 客户类型，影响文风


class PolishResult:
    """润色结果"""
    chapter_no: str
    content: str               # 润色后正文
    changes_summary: str       # 本轮修改摘要
    rounds_applied: int        # 实际执行轮次


async def polish_draft(
    drafts: list[DraftChapter],
    config: Optional[PolishConfig] = None,
) -> list[PolishResult]:
    """
    多轮润色节点

    每轮润色聚焦一个维度:
      Round 1 — 术语统一（行业术语、法规名称标准化）
      Round 2 — 文风适配（根据客户类型调整正式程度）+ 逻辑连贯性

    如果 Round 1 后无实质修改，提前终止。

    Args:
        drafts: Node 4 通过合规门禁的草稿章节
        config: 润色配置（轮次、维度、客户类型）

    Returns:
        润色后的章节列表
    """
    raise NotImplementedError("T5 骨架 — 待实现")
