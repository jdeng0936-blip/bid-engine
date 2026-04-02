"""
BidEngine Phase 1.2 — 七节点章节生成流水线

Pipeline:
  planner → retriever → writer → compliance_gate → polish_pipeline → reviewer → formatter

每个节点是一个独立 async 函数，通过 dict 传递上下文，支持单节点测试和整体编排。
"""
from app.services.generation.planner import plan_outline
from app.services.generation.retriever import retrieve_context
from app.services.generation.writer import generate_draft
from app.services.generation.compliance_gate import check_compliance
from app.services.generation.polish_pipeline import polish_draft
from app.services.generation.reviewer import review_scoring_coverage
from app.services.generation.formatter import format_and_persist

__all__ = [
    "plan_outline",
    "retrieve_context",
    "generate_draft",
    "check_compliance",
    "polish_draft",
    "review_scoring_coverage",
    "format_and_persist",
]
