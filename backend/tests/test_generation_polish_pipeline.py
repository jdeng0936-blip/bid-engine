"""
Node 5 polish_pipeline 单元测试 — 规则引擎 + Mock LLM
"""
import pytest
from unittest.mock import patch

from app.services.generation.polish_pipeline import (
    polish_draft,
    PolishConfig,
    PolishResult,
    _apply_terminology_rules,
    _TERMINOLOGY_MAP,
    _INFORMAL_MAP,
)
from app.services.generation.writer import DraftChapter


# ── 工厂函数 ──────────────────────────────────────────────

def _draft(chapter_no="第三章", title="食材采购与质量保障方案",
           content="本公司已通过ISO22000和haccp认证。", word_count=None):
    wc = word_count if word_count is not None else len(content)
    return DraftChapter(
        chapter_no=chapter_no, title=title,
        content=content, sources_cited=[], word_count=wc,
    )


def _long_content():
    return "本公司建立了完善的食品安全管理体系，通过ISO22000和haccp认证，冷库温度保持在0~4度范围。"


# ═══════════════════════════════════════════════════════════
# Round 1: 术语标准化规则
# ═══════════════════════════════════════════════════════════

class TestTerminologyRules:

    def test_iso22000_standardized(self):
        """ISO22000 → ISO 22000"""
        result, changes = _apply_terminology_rules("通过ISO22000认证")
        assert "ISO 22000" in result
        assert len(changes) >= 1

    def test_haccp_standardized(self):
        """haccp → HACCP"""
        result, changes = _apply_terminology_rules("haccp体系认证")
        assert "HACCP" in result

    def test_food_safety_law_standardized(self):
        """食品安全法 → 全称"""
        result, changes = _apply_terminology_rules("依据食品安全法第34条")
        assert "《中华人民共和国食品安全法》" in result

    def test_temperature_standardized(self):
        """0~4度 → 0~4℃"""
        result, _ = _apply_terminology_rules("冷藏温度0~4度")
        assert "\u2103" in result  # ℃

    def test_informal_replaced(self):
        """口语化用语被替换"""
        result, changes = _apply_terminology_rules("我们要搞好食品安全工作")
        assert "做好" in result
        assert "搞好" not in result

    def test_no_change_returns_empty(self):
        """无需修改时 changes 为空"""
        _, changes = _apply_terminology_rules("本公司已通过 HACCP 和 ISO 22000 认证。")
        assert len(changes) == 0

    def test_multiple_replacements(self):
        """多处替换同时生效"""
        text = "haccp和ISO22000和食品安全法"
        result, changes = _apply_terminology_rules(text)
        assert "HACCP" in result
        assert "ISO 22000" in result
        assert "《中华人民共和国食品安全法》" in result
        assert len(changes) == 3


# ═══════════════════════════════════════════════════════════
# polish_draft 主入口
# ═══════════════════════════════════════════════════════════

class TestPolishDraft:

    @pytest.mark.asyncio
    async def test_round1_only(self):
        """max_rounds=1 只执行术语标准化"""
        drafts = [_draft(content=_long_content())]
        config = PolishConfig(max_rounds=1, customer_type="school")

        results = await polish_draft(drafts, config)

        assert len(results) == 1
        r = results[0]
        assert "ISO 22000" in r.content
        assert "HACCP" in r.content
        assert r.rounds_applied == 1
        assert "术语标准化" in r.changes_summary

    @pytest.mark.asyncio
    @patch("app.services.generation.polish_pipeline._call_llm_polish")
    async def test_round2_with_llm(self, mock_llm):
        """max_rounds=2 执行术语 + LLM 文风润色"""
        polished_text = "【润色后】本公司建立了完善的食品安全管理体系。"
        mock_llm.return_value = polished_text

        drafts = [_draft(content=_long_content())]
        config = PolishConfig(max_rounds=2, customer_type="school")

        results = await polish_draft(drafts, config)

        r = results[0]
        assert r.content == polished_text
        assert r.rounds_applied == 2
        assert "LLM 文风适配" in r.changes_summary
        mock_llm.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.generation.polish_pipeline._call_llm_polish")
    async def test_llm_failure_keeps_round1(self, mock_llm):
        """LLM 失败时保留 Round 1 结果"""
        mock_llm.side_effect = RuntimeError("API 超时")

        drafts = [_draft(content="haccp认证体系")]
        config = PolishConfig(max_rounds=2, customer_type="school")

        results = await polish_draft(drafts, config)

        r = results[0]
        assert "HACCP" in r.content  # Round 1 结果保留
        assert "润色跳过" in r.changes_summary

    @pytest.mark.asyncio
    async def test_placeholder_chapter_skipped(self):
        """占位符章节（报价章）不做润色"""
        drafts = [_draft(
            chapter_no="第八章", title="报价文件",
            content="（报价数据由报价引擎自动生成）",
        )]

        results = await polish_draft(drafts, PolishConfig(max_rounds=2))

        r = results[0]
        assert r.rounds_applied == 0
        assert "跳过" in r.changes_summary

    @pytest.mark.asyncio
    async def test_empty_content_skipped(self):
        """空内容章节跳过"""
        drafts = [_draft(content="", word_count=0)]
        results = await polish_draft(drafts, PolishConfig())
        assert results[0].rounds_applied == 0

    @pytest.mark.asyncio
    async def test_multiple_chapters(self):
        """多章节逐一润色"""
        drafts = [
            _draft(chapter_no="第三章", content="ISO22000认证体系"),
            _draft(chapter_no="第四章", content="冷链温度0~4度"),
            _draft(chapter_no="第八章", content="（占位）"),
        ]
        config = PolishConfig(max_rounds=1)

        results = await polish_draft(drafts, config)

        assert len(results) == 3
        assert "ISO 22000" in results[0].content
        assert "\u2103" in results[1].content
        assert results[2].rounds_applied == 0

    @pytest.mark.asyncio
    async def test_preserves_chapter_metadata(self):
        """chapter_no 和 title 被正确透传"""
        drafts = [_draft(chapter_no="第五章", title="服务方案")]
        results = await polish_draft(drafts, PolishConfig(max_rounds=1))
        assert results[0].chapter_no == "第五章"
        assert results[0].title == "服务方案"

    @pytest.mark.asyncio
    async def test_custom_focus_dimensions(self):
        """仅配置 style 维度时跳过术语标准化"""
        drafts = [_draft(content="haccp认证")]
        config = PolishConfig(max_rounds=1, focus_dimensions=["style"])

        results = await polish_draft(drafts, config)

        r = results[0]
        # terminology 不在 focus_dimensions 中，haccp 不应被替换
        assert "haccp" in r.content
        # max_rounds=1 且 style 在 round2，所以 rounds_done 停在 0
        assert r.rounds_applied == 0
