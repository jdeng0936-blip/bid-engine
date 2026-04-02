"""
Node 2 retriever 单元测试 — Mock _retrieve_single_chapter
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass, field

from app.services.generation.retriever import (
    RetrievalResult,
    _build_query,
    retrieve_context,
)


# ── 复用 planner 的 ChapterPlan ──────────────────────────
@dataclass
class FakeChapterPlan:
    chapter_no: str
    title: str
    key_points: list = field(default_factory=list)
    mapped_requirements: list = field(default_factory=list)
    estimated_words: int = 800


# ── Mock 单章节检索结果 ──────────────────────────────────
def _make_retrieval_result(chapter_no: str) -> RetrievalResult:
    return RetrievalResult(
        chapter_no=chapter_no,
        std_clauses=[{
            "clause_no": "第34条", "doc_title": "食品安全法",
            "doc_type": "法律法规", "text": "食品经营者应当建立...",
        }],
        template_snippets=[{
            "chapter_name": "某中标案例-冷链方案", "text": "我公司采用全程温控...",
        }],
        bid_cases=[{
            "chapter_name": "某中标案例-冷链方案",
            "content": "我公司采用全程温控...", "distance": 0.2,
        }],
        table_data=[],
    )


_CHAPTER_NOS = ["第三章", "第四章", "第五章", "第六章", "第七章"]


def _make_plans(n: int = 3) -> list:
    """构造 n 个测试章节计划"""
    titles = ["食材采购与质量保障方案", "仓储管理与冷链配送方案", "服务方案与应急保障"]
    return [
        FakeChapterPlan(
            chapter_no=_CHAPTER_NOS[i],
            title=titles[i % len(titles)],
            key_points=["关键点A", "关键点B"],
        )
        for i in range(n)
    ]


class TestRetrieveContext:
    """retrieve_context 核心逻辑"""

    @pytest.mark.asyncio
    @patch("app.services.generation.retriever._retrieve_single_chapter")
    async def test_returns_results_for_each_chapter(self, mock_retrieve):
        """每个章节都应返回一个 RetrievalResult"""
        plans = _make_plans(3)
        mock_retrieve.side_effect = [
            _make_retrieval_result(p.chapter_no) for p in plans
        ]

        results = await retrieve_context(
            session=MagicMock(), tenant_id=1,
            chapter_plans=plans, project_id=1, top_k=5,
        )

        assert len(results) == 3
        assert results[0].chapter_no == "第三章"
        assert results[1].chapter_no == "第四章"
        assert results[2].chapter_no == "第五章"

    @pytest.mark.asyncio
    @patch("app.services.generation.retriever._retrieve_single_chapter")
    async def test_std_clauses_present(self, mock_retrieve):
        """std_clauses 被正确返回"""
        plans = _make_plans(1)
        mock_retrieve.return_value = _make_retrieval_result("第三章")

        results = await retrieve_context(
            session=MagicMock(), tenant_id=1,
            chapter_plans=plans, project_id=1,
        )

        r = results[0]
        assert len(r.std_clauses) == 1
        assert r.std_clauses[0]["doc_title"] == "食品安全法"

    @pytest.mark.asyncio
    @patch("app.services.generation.retriever._retrieve_single_chapter")
    async def test_template_snippets_present(self, mock_retrieve):
        """template_snippets 被正确返回"""
        plans = _make_plans(1)
        mock_retrieve.return_value = _make_retrieval_result("第三章")

        results = await retrieve_context(
            session=MagicMock(), tenant_id=1,
            chapter_plans=plans, project_id=1,
        )

        r = results[0]
        assert len(r.template_snippets) == 1
        assert "冷链" in r.template_snippets[0]["chapter_name"]

    @pytest.mark.asyncio
    @patch("app.services.generation.retriever._retrieve_single_chapter")
    async def test_bid_cases_present(self, mock_retrieve):
        """bid_cases 被正确返回"""
        plans = _make_plans(1)
        mock_retrieve.return_value = _make_retrieval_result("第三章")

        results = await retrieve_context(
            session=MagicMock(), tenant_id=1,
            chapter_plans=plans, project_id=1,
        )

        assert len(results[0].bid_cases) == 1

    @pytest.mark.asyncio
    @patch("app.services.generation.retriever._retrieve_single_chapter")
    async def test_graceful_on_retrieval_error(self, mock_retrieve):
        """单章节检索失败不影响其他章节"""
        plans = _make_plans(3)
        mock_retrieve.side_effect = [
            _make_retrieval_result("第三章"),
            RuntimeError("模拟检索失败"),
            _make_retrieval_result("第五章"),
        ]

        results = await retrieve_context(
            session=MagicMock(), tenant_id=1,
            chapter_plans=plans, project_id=1,
        )

        assert len(results) == 3
        # 第一个和第三个正常
        assert len(results[0].std_clauses) == 1
        assert len(results[2].std_clauses) == 1
        # 第二个失败 → 空结果
        assert results[1].std_clauses == []
        assert results[1].template_snippets == []

    @pytest.mark.asyncio
    @patch("app.services.generation.retriever._retrieve_single_chapter")
    async def test_empty_plans(self, mock_retrieve):
        """空章节计划 → 空结果"""
        results = await retrieve_context(
            session=MagicMock(), tenant_id=1,
            chapter_plans=[], project_id=1,
        )
        assert results == []
        mock_retrieve.assert_not_called()


class TestBuildQuery:
    """_build_query 辅助函数"""

    def test_includes_title_and_key_points(self):
        plan = FakeChapterPlan(
            chapter_no="第三章",
            title="食材采购与质量保障方案",
            key_points=["食材溯源", "农残检测", "供应商管理", "多余的第四个"],
        )
        query = _build_query(plan)
        assert "食材采购与质量保障方案" in query
        assert "食材溯源" in query
        assert "农残检测" in query
        assert "供应商管理" in query
        # 只取前 3 个
        assert "多余的第四个" not in query

    def test_title_only_when_no_key_points(self):
        plan = FakeChapterPlan(chapter_no="第一章", title="投标函", key_points=[])
        query = _build_query(plan)
        assert query == "投标函"
