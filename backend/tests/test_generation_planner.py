"""
Node 1 planner 单元测试 — Mock LLM + Mock DB
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass


# ── 模拟 TenderRequirement ──────────────────────────────
@dataclass
class FakeRequirement:
    id: int
    content: str
    category: str
    max_score: float = None
    score_weight: float = None
    is_mandatory: bool = True


# ── 模拟 BidProject ─────────────────────────────────────
@dataclass
class FakeProject:
    id: int = 1
    customer_type: str = "school"
    project_name: str = "测试学校食材配送项目"
    requirements: list = None

    def __post_init__(self):
        if self.requirements is None:
            self.requirements = [
                FakeRequirement(1, "投标人须持有食品经营许可证", "disqualification"),
                FakeRequirement(2, "冷链配送方案及温控措施", "scoring", max_score=15.0),
                FakeRequirement(3, "人员配置及培训计划", "scoring", max_score=10.0),
                FakeRequirement(4, "质量管理体系认证情况", "qualification"),
            ]


# ── 模拟 LLM 返回 ────────────────────────────────────────
_MOCK_LLM_RESPONSE = json.dumps({"chapters": [
    {"chapter_no": "第一章", "key_points": ["投标函格式规范", "法人授权书"], "estimated_words": 400},
    {"chapter_no": "第二章", "key_points": ["营业执照", "食品经营许可证", "企业信用报告"], "estimated_words": 600},
    {"chapter_no": "第三章", "key_points": ["食材溯源体系", "农残检测", "供应商管理"], "estimated_words": 1500},
    {"chapter_no": "第四章", "key_points": ["冷链温控方案", "GPS实时监控", "配送时效"], "estimated_words": 1200},
    {"chapter_no": "第五章", "key_points": ["应急预案", "投诉响应机制"], "estimated_words": 800},
    {"chapter_no": "第六章", "key_points": ["营养师配置", "健康证管理"], "estimated_words": 800},
    {"chapter_no": "第七章", "key_points": ["HACCP体系", "ISO22000认证"], "estimated_words": 800},
    {"chapter_no": "第八章", "key_points": ["报价明细表", "下浮率说明"], "estimated_words": 400},
    {"chapter_no": "第九章", "key_points": ["历史中标案例", "荣誉证书"], "estimated_words": 500},
]})


def _make_mock_llm_response(content: str):
    """构造 OpenAI ChatCompletion 样式的 mock 响应"""
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


class TestPlanOutline:
    """plan_outline 核心逻辑测试"""

    @pytest.mark.asyncio
    @patch("app.services.generation.planner._call_llm_for_key_points")
    async def test_returns_9_chapters(self, mock_llm):
        """标准 9 章结构"""
        mock_llm.return_value = json.loads(_MOCK_LLM_RESPONSE)["chapters"]

        from app.services.generation.planner import plan_outline
        plans = await plan_outline(
            session=MagicMock(),
            project=FakeProject(),
            customer_type="school",
        )
        assert len(plans) == 9
        chapter_nos = [p.chapter_no for p in plans]
        assert chapter_nos[0] == "第一章"
        assert chapter_nos[-1] == "第九章"

    @pytest.mark.asyncio
    @patch("app.services.generation.planner._call_llm_for_key_points")
    async def test_key_points_from_llm(self, mock_llm):
        """LLM 返回的 key_points 被正确填入"""
        mock_llm.return_value = json.loads(_MOCK_LLM_RESPONSE)["chapters"]

        from app.services.generation.planner import plan_outline
        plans = await plan_outline(session=MagicMock(), project=FakeProject())

        ch3 = next(p for p in plans if p.chapter_no == "第三章")
        assert "食材溯源体系" in ch3.key_points
        assert ch3.estimated_words == 1500

    @pytest.mark.asyncio
    @patch("app.services.generation.planner._call_llm_for_key_points")
    async def test_mapped_requirements(self, mock_llm):
        """评分标准被正确映射到对应章节"""
        mock_llm.return_value = json.loads(_MOCK_LLM_RESPONSE)["chapters"]

        from app.services.generation.planner import plan_outline
        plans = await plan_outline(session=MagicMock(), project=FakeProject())

        # "冷链配送方案及温控措施" (id=2) 应映射到第四章
        ch4 = next(p for p in plans if p.chapter_no == "第四章")
        assert 2 in ch4.mapped_requirements

    @pytest.mark.asyncio
    @patch("app.services.generation.planner._call_llm_for_key_points")
    async def test_fallback_on_llm_failure(self, mock_llm):
        """LLM 失败时降级到纯模板方案"""
        mock_llm.side_effect = RuntimeError("LLM 不可用")

        from app.services.generation.planner import plan_outline
        plans = await plan_outline(session=MagicMock(), project=FakeProject())

        # 仍然返回 9 章
        assert len(plans) == 9
        # 关键点来自模板 keywords 或 requirement content
        assert all(len(p.key_points) > 0 for p in plans)


class TestBuildPlansFromTemplates:
    """_build_plans_from_templates fallback 逻辑"""

    def test_no_requirements(self):
        from app.services.generation.planner import _build_plans_from_templates
        from app.services.bid_chapter_engine import get_chapter_templates

        templates = get_chapter_templates("school")
        plans = _build_plans_from_templates(templates, {t["chapter_no"]: [] for t in templates})

        assert len(plans) == 9
        # 无 requirements 时 key_points 来自模板 keywords
        assert all(len(p.key_points) > 0 for p in plans)
        assert all(p.estimated_words == 600 for p in plans)

    def test_with_requirements(self):
        from app.services.generation.planner import _build_plans_from_templates
        from app.services.bid_chapter_engine import get_chapter_templates

        templates = get_chapter_templates("school")
        req_mapping = {t["chapter_no"]: [] for t in templates}
        req_mapping["第三章"] = [
            {"id": 10, "content": "食品安全管理体系说明", "category": "scoring", "max_score": 20},
        ]

        plans = _build_plans_from_templates(templates, req_mapping)
        ch3 = next(p for p in plans if p.chapter_no == "第三章")
        assert 10 in ch3.mapped_requirements
        assert ch3.estimated_words == 1200  # 有 requirements → 1200
