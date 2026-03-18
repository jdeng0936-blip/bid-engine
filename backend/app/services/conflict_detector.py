"""
规则冲突检测引擎 — 分析规则库中的逻辑冲突

检测维度:
  1. 条件矛盾型冲突（同 field 同 operator 不同 value 的两条规则指向矛盾结论）
  2. 完全覆盖型冲突（A 规则条件是 B 规则条件的子集但结论不同）
  3. 优先级歧义（同条件命中多条规则但优先级相同）
"""
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.rule import RuleGroup, Rule, RuleCondition, RuleAction


# ========== Schema ==========

class ConflictItem(BaseModel):
    """冲突项"""
    type: str = Field(description="冲突类型: condition_clash / priority_ambiguity / overlap")
    severity: str = Field(description="严重程度: error / warning")
    rule_a_id: int
    rule_a_name: str
    rule_b_id: int
    rule_b_name: str
    field: str = Field(default="", description="冲突字段")
    detail: str = Field(description="冲突详细描述")
    suggestion: str = Field(default="", description="修改建议")


class ConflictResult(BaseModel):
    """规则冲突检测结果"""
    total_rules: int = Field(description="分析的规则总数")
    total_conflicts: int = Field(description="发现的冲突数")
    errors: int = Field(description="严重冲突数")
    warnings: int = Field(description="警告数")
    conflicts: list[ConflictItem] = Field(default_factory=list)


# ========== 检测引擎 ==========

class ConflictDetector:
    """规则冲突检测器"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def detect(self, group_id: Optional[int] = None) -> ConflictResult:
        """
        检测规则冲突

        Args:
            group_id: 指定规则组 ID，None 表示检测全部

        Returns:
            ConflictResult
        """
        # 读取规则（含条件和结论）
        stmt = select(Rule).options(
            selectinload(Rule.conditions),
            selectinload(Rule.actions),
        ).where(Rule.is_active == True)

        if group_id is not None:
            stmt = stmt.where(Rule.group_id == group_id)

        result = await self.session.execute(stmt)
        rules = list(result.scalars().all())

        if len(rules) < 2:
            return ConflictResult(
                total_rules=len(rules), total_conflicts=0,
                errors=0, warnings=0, conflicts=[],
            )

        conflicts: list[ConflictItem] = []

        # 两两比较规则
        for i in range(len(rules)):
            for j in range(i + 1, len(rules)):
                rule_a, rule_b = rules[i], rules[j]

                # 仅比较同 category 的规则（不同类别不太可能冲突）
                if rule_a.category != rule_b.category:
                    continue

                # 1. 条件矛盾型冲突
                cond_conflicts = self._check_condition_clash(rule_a, rule_b)
                conflicts.extend(cond_conflicts)

                # 2. 优先级歧义
                prio_conflicts = self._check_priority_ambiguity(rule_a, rule_b)
                conflicts.extend(prio_conflicts)

                # 3. 完全覆盖
                overlap_conflicts = self._check_overlap(rule_a, rule_b)
                conflicts.extend(overlap_conflicts)

        n_errors = sum(1 for c in conflicts if c.severity == "error")
        n_warnings = sum(1 for c in conflicts if c.severity == "warning")

        return ConflictResult(
            total_rules=len(rules),
            total_conflicts=len(conflicts),
            errors=n_errors,
            warnings=n_warnings,
            conflicts=conflicts,
        )

    def _check_condition_clash(self, a: Rule, b: Rule) -> list[ConflictItem]:
        """检测两条规则是否在同字段上有矛盾条件但目标章节相同"""
        conflicts = []
        a_conds = {c.field: c for c in a.conditions}
        b_conds = {c.field: c for c in b.conditions}

        # 两规则目标相同章节
        a_chapters = {act.target_chapter for act in a.actions}
        b_chapters = {act.target_chapter for act in b.actions}
        if not a_chapters.intersection(b_chapters):
            return []

        # 检查同字段同运算符不同值
        for field in set(a_conds.keys()) & set(b_conds.keys()):
            ca, cb = a_conds[field], b_conds[field]
            if ca.operator == cb.operator and ca.value != cb.value:
                # 同字段同运算符不同值 → 可能矛盾
                if ca.operator == "eq":
                    conflicts.append(ConflictItem(
                        type="condition_clash",
                        severity="error",
                        rule_a_id=a.id, rule_a_name=a.name,
                        rule_b_id=b.id, rule_b_name=b.name,
                        field=field,
                        detail=f"字段 {field}: 规则A要求={ca.value}，规则B要求={cb.value}，二者不可能同时满足但指向相同章节",
                        suggestion=f"检查字段 {field} 的条件值，确认是否需要合并或区分",
                    ))

        return conflicts

    def _check_priority_ambiguity(self, a: Rule, b: Rule) -> list[ConflictItem]:
        """检测两条条件完全相同但优先级相同的规则"""
        if a.priority != b.priority:
            return []

        # 条件集合相同？
        a_cond_set = {(c.field, c.operator, c.value) for c in a.conditions}
        b_cond_set = {(c.field, c.operator, c.value) for c in b.conditions}

        if a_cond_set == b_cond_set and len(a_cond_set) > 0:
            return [ConflictItem(
                type="priority_ambiguity",
                severity="warning",
                rule_a_id=a.id, rule_a_name=a.name,
                rule_b_id=b.id, rule_b_name=b.name,
                detail=f"条件完全相同但优先级都是 {a.priority}，运行时执行顺序不确定",
                suggestion="给其中一条规则增加优先级区分",
            )]
        return []

    def _check_overlap(self, a: Rule, b: Rule) -> list[ConflictItem]:
        """检测 A 的条件集合是否完全包含 B（即 A 更严格，B 更宽泛）"""
        a_cond_set = {(c.field, c.operator, c.value) for c in a.conditions}
        b_cond_set = {(c.field, c.operator, c.value) for c in b.conditions}

        if not a_cond_set or not b_cond_set:
            return []

        # A 是 B 的真子集 → B 覆盖 A
        if a_cond_set < b_cond_set or b_cond_set < a_cond_set:
            narrower = a if len(a_cond_set) > len(b_cond_set) else b
            broader = b if len(a_cond_set) > len(b_cond_set) else a

            # 检查结论是否不同
            a_chapters = {act.target_chapter for act in narrower.actions}
            b_chapters = {act.target_chapter for act in broader.actions}

            if a_chapters != b_chapters:
                return [ConflictItem(
                    type="overlap",
                    severity="warning",
                    rule_a_id=narrower.id, rule_a_name=narrower.name,
                    rule_b_id=broader.id, rule_b_name=broader.name,
                    detail=f"「{narrower.name}」的条件是「{broader.name}」的子集，但目标章节不同",
                    suggestion=f"确认「{broader.name}」在更宽泛场景下的结论是否应覆盖「{narrower.name}」",
                )]
        return []
