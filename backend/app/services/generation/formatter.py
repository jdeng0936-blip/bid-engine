"""
Node 7: 格式化持久化 — 写入 BidChapter.content + SSE 实时推送

流水线终节点，负责将最终内容持久化到数据库并通过 SSE 通知前端。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator, Optional

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.bid_project import BidChapter

from app.services.generation.reviewer import ReviewReport


class FormatResult:
    """格式化输出"""
    chapter_id: int            # 持久化后的 BidChapter.id
    chapter_no: str
    title: str
    word_count: int
    status: str                # "generated" / "needs_review"


async def format_and_persist(
    session: AsyncSession,
    project_id: int,
    review_report: ReviewReport,
    sse_enabled: bool = True,
) -> list[FormatResult]:
    """
    格式化持久化节点

    将校验通过的章节内容写入 BidChapter 表，更新状态为 generated。
    覆盖率不足的章节标记为 needs_review。
    如果开启 SSE，逐章推送生成进度到前端。

    Args:
        session: 数据库会话
        project_id: 投标项目 ID
        review_report: Node 6 输出的覆盖校验报告
        sse_enabled: 是否通过 SSE 推送进度

    Returns:
        各章节的持久化结果

    Yields (when used as SSE generator):
        JSON 格式的进度事件: {"chapter_no": "...", "status": "...", "progress": 0.x}
    """
    raise NotImplementedError("T5 骨架 — 待实现")


async def stream_generation_progress(
    session: AsyncSession,
    project_id: int,
    review_report: ReviewReport,
) -> AsyncGenerator[str, None]:
    """
    SSE 流式推送入口

    逐章持久化并推送进度事件，供 FastAPI StreamingResponse 使用。

    Args:
        session: 数据库会话
        project_id: 投标项目 ID
        review_report: Node 6 输出的覆盖校验报告

    Yields:
        SSE 格式字符串: "data: {...}\\n\\n"
    """
    raise NotImplementedError("T5 骨架 — 待实现")
