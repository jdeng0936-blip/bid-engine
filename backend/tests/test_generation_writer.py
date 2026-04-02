"""
Node 3 writer 单元测试 — Mock LLM 调用
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass, field

from app.services.generation.writer import (
    DraftChapter,
    generate_draft,
    _build_rag_block,
    _build_key_points_text,
    _extract_sources,
    _QUOTATION_CHAPTER,
)
from app.services.generation.planner import ChapterPlan
from app.services.generation.retriever import RetrievalResult


# ── Fake 对象 ─────────────────────────────────────────────

@dataclass
class FakeProject:
    id: int = 1
    project_name: str = "测试学校食材配送项目"
    customer_type: str = "school"
    tender_org: str = "XX市第一小学"
    budget_amount: float = 500000.0
    delivery_scope: str = "校区食堂"
    delivery_period: str = "一年"
    enterprise_id: int = 1
    requirements: list = field(default_factory=list)


def _make_plans() -> list[ChapterPlan]:
    return [
        ChapterPlan(chapter_no="第三章", title="食材采购与质量保障方案",
                     key_points=["食材溯源", "农残检测"], estimated_words=1200),
        ChapterPlan(chapter_no="第八章", title="报价文件",
                     key_points=["报价明细"], estimated_words=400),
        ChapterPlan(chapter_no="第九章", title="业绩案例与荣誉证书",
                     key_points=["历史中标案例"], estimated_words=500),
    ]


def _make_retrievals() -> list[RetrievalResult]:
    return [
        RetrievalResult(
            chapter_no="第三章",
            std_clauses=[{"doc_title": "食品安全法", "clause_no": "第34条",
                          "text": "食品经营者应当建立食品安全追溯体系"}],
            template_snippets=[{"chapter_name": "模板-质量方案", "text": "农残检测覆盖率100%"}],
            bid_cases=[{"chapter_name": "XX学校中标案例", "content": "我公司采用全程溯源体系"}],
        ),
        RetrievalResult(chapter_no="第八章"),
        RetrievalResult(
            chapter_no="第九章",
            std_clauses=[],
            bid_cases=[{"chapter_name": "历史业绩汇总", "content": "累计服务学校50余所"}],
        ),
    ]


_MOCK_LLM_CONTENT = "本公司建立了完善的食材采购与质量保障体系，覆盖从田间到餐桌的全流程管控。"


class TestGenerateDraft:
    """generate_draft 核心逻辑"""

    @pytest.mark.asyncio
    @patch("app.services.generation.writer._call_llm")
    async def test_returns_all_chapters(self, mock_llm):
        """输出数量与输入章节计划一致"""
        mock_llm.return_value = _MOCK_LLM_CONTENT
        plans = _make_plans()
        retrievals = _make_retrievals()

        drafts = await generate_draft(
            session=MagicMock(), project=FakeProject(),
            chapter_plans=plans, retrieval_results=retrievals,
        )
        assert len(drafts) == 3

    @pytest.mark.asyncio
    @patch("app.services.generation.writer._call_llm")
    async def test_quotation_chapter_skipped(self, mock_llm):
        """报价章节不调用 LLM"""
        mock_llm.return_value = _MOCK_LLM_CONTENT
        plans = _make_plans()
        retrievals = _make_retrievals()

        drafts = await generate_draft(
            session=MagicMock(), project=FakeProject(),
            chapter_plans=plans, retrieval_results=retrievals,
        )
        ch8 = next(d for d in drafts if d.chapter_no == _QUOTATION_CHAPTER)
        assert "报价引擎" in ch8.content
        assert ch8.word_count == 0
        # LLM 只被调用 2 次（第三章 + 第九章）
        assert mock_llm.call_count == 2

    @pytest.mark.asyncio
    @patch("app.services.generation.writer._call_llm")
    async def test_content_from_llm(self, mock_llm):
        """LLM 返回内容被写入 draft"""
        mock_llm.return_value = _MOCK_LLM_CONTENT

        drafts = await generate_draft(
            session=MagicMock(), project=FakeProject(),
            chapter_plans=_make_plans(), retrieval_results=_make_retrievals(),
        )
        ch3 = next(d for d in drafts if d.chapter_no == "第三章")
        assert ch3.content == _MOCK_LLM_CONTENT
        assert ch3.word_count == len(_MOCK_LLM_CONTENT)

    @pytest.mark.asyncio
    @patch("app.services.generation.writer._call_llm")
    async def test_sources_cited(self, mock_llm):
        """sources_cited 从检索结果提取"""
        mock_llm.return_value = _MOCK_LLM_CONTENT

        drafts = await generate_draft(
            session=MagicMock(), project=FakeProject(),
            chapter_plans=_make_plans(), retrieval_results=_make_retrievals(),
        )
        ch3 = next(d for d in drafts if d.chapter_no == "第三章")
        assert "食品安全法 第34条" in ch3.sources_cited
        assert "XX学校中标案例" in ch3.sources_cited

    @pytest.mark.asyncio
    @patch("app.services.generation.writer._call_llm")
    async def test_llm_failure_graceful(self, mock_llm):
        """LLM 失败时不中断，章节内容标记失败原因"""
        mock_llm.side_effect = RuntimeError("API 超时")

        drafts = await generate_draft(
            session=MagicMock(), project=FakeProject(),
            chapter_plans=[ChapterPlan(chapter_no="第三章", title="测试章节")],
            retrieval_results=[RetrievalResult(chapter_no="第三章")],
        )
        assert len(drafts) == 1
        assert "生成失败" in drafts[0].content

    @pytest.mark.asyncio
    @patch("app.services.generation.writer._call_llm")
    async def test_enterprise_info_passed(self, mock_llm):
        """enterprise_info 被传入 prompt"""
        mock_llm.return_value = _MOCK_LLM_CONTENT

        await generate_draft(
            session=MagicMock(), project=FakeProject(),
            chapter_plans=[ChapterPlan(chapter_no="第三章", title="测试")],
            retrieval_results=[RetrievalResult(chapter_no="第三章")],
            enterprise_info="测试企业：XX食品有限公司",
        )
        # 检查 LLM 被调用时 prompt 中包含企业信息
        prompt_arg = mock_llm.call_args[0][0]
        assert "XX食品有限公司" in prompt_arg


class TestBuildRagBlock:
    """_build_rag_block 辅助函数"""

    def test_with_all_sources(self):
        r = RetrievalResult(
            chapter_no="第三章",
            std_clauses=[{"doc_title": "食品安全法", "clause_no": "第34条", "text": "内容A"}],
            template_snippets=[{"chapter_name": "模板X", "text": "内容B"}],
            bid_cases=[{"chapter_name": "案例Y", "content": "内容C"}],
        )
        block = _build_rag_block(r)
        assert "法规标准参考" in block
        assert "食品安全法" in block
        assert "知识库模板片段" in block
        assert "历史中标案例参考" in block

    def test_empty_retrieval(self):
        r = RetrievalResult(chapter_no="第一章")
        block = _build_rag_block(r)
        assert "暂无相关参考资料" in block


class TestExtractSources:
    """_extract_sources 辅助函数"""

    def test_extracts_clause_titles(self):
        r = RetrievalResult(
            chapter_no="第三章",
            std_clauses=[
                {"doc_title": "食品安全法", "clause_no": "第34条"},
                {"doc_title": "GB/T 22918", "clause_no": ""},
            ],
            bid_cases=[{"chapter_name": "中标案例A", "content": "..."}],
        )
        sources = _extract_sources(r)
        assert "食品安全法 第34条" in sources
        assert "GB/T 22918" in sources
        assert "中标案例A" in sources

    def test_empty(self):
        r = RetrievalResult(chapter_no="第一章")
        assert _extract_sources(r) == []


class TestBuildKeyPointsText:
    """_build_key_points_text 辅助函数"""

    def test_numbered_list(self):
        plan = ChapterPlan(chapter_no="第三章", title="T", key_points=["A", "B", "C"])
        text = _build_key_points_text(plan)
        assert "1. A" in text
        assert "3. C" in text

    def test_empty(self):
        plan = ChapterPlan(chapter_no="第一章", title="T", key_points=[])
        assert "无特定关键点" in _build_key_points_text(plan)
