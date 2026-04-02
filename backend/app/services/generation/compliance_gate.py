"""
Node 4: 合规门禁 — L1 格式检查 + L2 语义审查 + L3 废标检测

任何一项 L3 检测失败将阻断流水线并返回修复建议。
"""
from enum import Enum
from typing import Optional

from app.services.generation.writer import DraftChapter


class ComplianceLevel(str, Enum):
    L1_FORMAT = "format"       # 格式规范（字数/标题/编号）
    L2_SEMANTIC = "semantic"   # 语义合规（法规引用/术语准确性）
    L3_DISQUALIFY = "disqualify"  # 废标项检测（触发即出局）


class ComplianceIssue:
    """单个合规问题"""
    level: ComplianceLevel
    chapter_no: str
    description: str
    suggestion: str            # 修复建议
    is_blocking: bool          # L3 为 True，L1/L2 为 False


class ComplianceReport:
    """合规门禁报告"""
    passed: bool               # 是否全部通过（无 blocking issue）
    issues: list[ComplianceIssue]
    chapters: list[DraftChapter]  # 原样透传或标注问题后的章节


async def check_compliance(
    drafts: list[DraftChapter],
    requirements: list[dict],
    enterprise_cred_types: Optional[set[str]] = None,
) -> ComplianceReport:
    """
    合规门禁节点

    三层递进检查:
      L1 格式 — 章节编号连续性、标题规范、字数下限
      L2 语义 — 法规引用准确性、术语一致性（调用 LLM）
      L3 废标 — 匹配废标项关键词，检测资质缺失等致命问题

    Args:
        drafts: Node 3 输出的草稿章节
        requirements: 招标要求列表（含 category 字段区分废标/资格/评分）
        enterprise_cred_types: 企业已有资质类型集合，用于 L3 资质匹配

    Returns:
        合规报告，passed=False 时流水线应暂停等待修复
    """
    raise NotImplementedError("T5 骨架 — 待实现")
