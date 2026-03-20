"""
批量合规校验引擎 — 对项目参数 + 用户设计值进行全方位合规检查

校验维度:
  1. 支护参数（锚杆间排距、锚索数量）
  2. 通风参数（需风量、风速）
  3. 断面参数（最小净面积、宽高比）
  4. 安全参数（瓦斯等级对应措施、自燃对应措施）

返回: 多维度合规报告 + 不合规项列表 + 整改建议
"""
from pydantic import BaseModel, Field
from typing import Literal

from app.schemas.calc import SupportCalcInput, CalcWarning
from app.schemas.vent import VentCalcInput
from app.services.calc_engine import SupportCalcEngine
from app.services.vent_engine import VentCalcEngine


# ========== Schema ==========

class ComplianceInput(BaseModel):
    """批量合规校验输入 — 项目全参数"""
    # 地质条件
    rock_class: Literal["I", "II", "III", "IV", "V"] = Field(description="围岩级别")
    gas_level: str = Field(default="低瓦斯", description="瓦斯等级")
    coal_thickness: float = Field(default=3.0, description="煤层厚度 m")
    spontaneous_combustion: str = Field(default="不易自燃", description="自燃倾向性")

    # 巷道参数
    roadway_type: str = Field(default="进风巷", description="巷道类型(进风巷/回风巷/高抽巷/低抽巷/切巷/运输巷/联络巷/石门)")
    section_form: Literal["矩形", "拱形", "梯形"] = Field(default="矩形", description="断面形式")
    section_width: float = Field(default=4.5, gt=0, description="断面宽度 m")
    section_height: float = Field(default=3.2, gt=0, description="断面高度 m")
    excavation_length: float = Field(default=600, gt=0, description="掘进长度 m")

    # 支护设计值（可选，填了就校核）
    bolt_spacing: float = Field(default=800, description="设计锚杆间距 mm")
    bolt_row_spacing: float = Field(default=800, description="设计锚杆排距 mm")
    cable_count: int = Field(default=3, description="设计锚索数量/排")

    # 通风设计值
    gas_emission: float = Field(default=1.0, description="瓦斯涌出量 m³/min")
    design_air_volume: float = Field(default=0, description="设计风量 m³/min（0=不校核）")
    max_workers: int = Field(default=25, description="最多同时工作人数")


class ComplianceItem(BaseModel):
    """单项合规检查结果"""
    category: str = Field(description="检查类别")
    item: str = Field(description="检查项")
    status: Literal["pass", "fail", "warning"] = Field(description="合规状态")
    message: str = Field(description="说明")
    suggestion: str = Field(default="", description="整改建议")


class ComplianceResult(BaseModel):
    """批量合规校验结果"""
    total_checks: int = Field(description="总检查项数")
    passed: int = Field(description="通过数")
    failed: int = Field(description="不合规数")
    warned: int = Field(description="预警数")
    is_compliant: bool = Field(description="总体是否合规（无 fail 即合规）")
    items: list[ComplianceItem] = Field(default_factory=list)


# ========== 校验引擎 ==========

# 围岩级别 → 最小净断面积要求（m²）（参考《煤矿安全规程》）
MIN_SECTION_AREA = {"I": 6.0, "II": 7.0, "III": 8.0, "IV": 9.0, "V": 10.0}

# 断面最小高度（m）
MIN_HEIGHT = 2.5


class ComplianceEngine:
    """批量合规校验引擎 — 无状态纯函数"""

    @staticmethod
    def check(inp: ComplianceInput) -> ComplianceResult:
        items: list[ComplianceItem] = []

        # ========== 1. 断面校核 ==========
        area = inp.section_width * inp.section_height
        min_area = MIN_SECTION_AREA.get(inp.rock_class, 8.0)

        items.append(ComplianceItem(
            category="断面", item="净断面积",
            status="pass" if area >= min_area else "fail",
            message=f"净面积 {area:.1f}m² {'≥' if area >= min_area else '<'} 要求 {min_area}m²",
            suggestion="" if area >= min_area else f"建议增大断面，至少 {min_area}m²",
        ))

        items.append(ComplianceItem(
            category="断面", item="最小高度",
            status="pass" if inp.section_height >= MIN_HEIGHT else "fail",
            message=f"净高 {inp.section_height}m {'≥' if inp.section_height >= MIN_HEIGHT else '<'} 要求 {MIN_HEIGHT}m",
            suggestion="" if inp.section_height >= MIN_HEIGHT else f"净高不得低于 {MIN_HEIGHT}m",
        ))

        # ========== 2. 支护参数校核 ==========
        support_input = SupportCalcInput(
            rock_class=inp.rock_class,
            section_form=inp.section_form,
            section_width=inp.section_width,
            section_height=inp.section_height,
            bolt_spacing=inp.bolt_spacing,
            bolt_row_spacing=inp.bolt_row_spacing,
            cable_count=inp.cable_count,
        )
        support_result = SupportCalcEngine.calculate(support_input)

        # 锚杆间距
        items.append(ComplianceItem(
            category="支护", item="锚杆间距",
            status="pass" if inp.bolt_spacing <= support_result.max_bolt_spacing else "fail",
            message=f"设计 {inp.bolt_spacing}mm {'≤' if inp.bolt_spacing <= support_result.max_bolt_spacing else '>'} 最大 {support_result.max_bolt_spacing}mm",
            suggestion="" if inp.bolt_spacing <= support_result.max_bolt_spacing else f"应 ≤ {support_result.max_bolt_spacing}mm",
        ))

        # 锚杆排距
        items.append(ComplianceItem(
            category="支护", item="锚杆排距",
            status="pass" if inp.bolt_row_spacing <= support_result.max_bolt_row_spacing else "fail",
            message=f"设计 {inp.bolt_row_spacing}mm {'≤' if inp.bolt_row_spacing <= support_result.max_bolt_row_spacing else '>'} 最大 {support_result.max_bolt_row_spacing}mm",
            suggestion="" if inp.bolt_row_spacing <= support_result.max_bolt_row_spacing else f"应 ≤ {support_result.max_bolt_row_spacing}mm",
        ))

        # 锚索数量
        items.append(ComplianceItem(
            category="支护", item="锚索数量",
            status="pass" if inp.cable_count >= support_result.min_cable_count else "fail",
            message=f"设计 {inp.cable_count} 根 {'≥' if inp.cable_count >= support_result.min_cable_count else '<'} 最少 {support_result.min_cable_count} 根",
            suggestion="" if inp.cable_count >= support_result.min_cable_count else f"至少 {support_result.min_cable_count} 根",
        ))

        # ========== 3. 通风校核 ==========
        if inp.design_air_volume > 0:
            vent_input = VentCalcInput(
                gas_emission=inp.gas_emission,
                gas_level=inp.gas_level,
                section_area=area,
                excavation_length=inp.excavation_length,
                max_workers=inp.max_workers,
                design_air_volume=inp.design_air_volume,
            )
            vent_result = VentCalcEngine.calculate(vent_input)

            items.append(ComplianceItem(
                category="通风", item="需风量校核",
                status="pass" if inp.design_air_volume >= vent_result.required_air_volume else "fail",
                message=f"设计 {inp.design_air_volume}m³/min {'≥' if inp.design_air_volume >= vent_result.required_air_volume else '<'} 需求 {vent_result.required_air_volume}m³/min",
                suggestion="" if inp.design_air_volume >= vent_result.required_air_volume else f"风量不足，至少 {vent_result.required_air_volume}m³/min",
            ))

        # ========== 4. 安全措施校核 ==========
        # 高瓦斯/突出矿井特殊要求
        if inp.gas_level in ("高瓦斯", "突出"):
            items.append(ComplianceItem(
                category="安全", item="瓦斯等级措施",
                status="warning",
                message=f"{inp.gas_level}矿井，须加强瓦斯监测和防突措施",
                suggestion="应配置瓦斯断电仪、加强日常巡检、编制防突专项安全技术措施",
            ))

        # 自燃倾向性
        if inp.spontaneous_combustion in ("自燃", "容易自燃"):
            items.append(ComplianceItem(
                category="安全", item="自燃防控",
                status="warning",
                message=f"煤层{inp.spontaneous_combustion}，须编制防灭火专项措施",
                suggestion="落实注氮/灌浆等防灭火措施，配备束管监测系统",
            ))

        # ========== 5. 巷道类型专项校核 ==========
        roadway = getattr(inp, 'roadway_type', '进风巷')

        # 高抽巷 / 低抽巷 — 瓦斯抽放巷道专项要求
        if roadway in ('高抽巷', '低抽巷'):
            items.append(ComplianceItem(
                category="巷道类型", item="瓦斯抽放巷道专项",
                status="warning",
                message=f"【{roadway}】属于瓦斯抽放巷道，须编制瓦斯抽采专项安全技术措施",
                suggestion="须明确抽采钻孔布置参数、封孔工艺、管路敷设方式及抽采达标指标",
            ))
            items.append(ComplianceItem(
                category="巷道类型", item=f"{roadway}密闭管理",
                status="warning",
                message=f"【{roadway}】须设置密闭墙，配备束管监测系统和安全监控传感器",
                suggestion="密闭墙两侧须安设CO/CH4/O2传感器，并接入安全监控系统",
            ))
            # 高抽巷特殊要求
            if roadway == '高抽巷':
                items.append(ComplianceItem(
                    category="巷道类型", item="高抽巷层位控制",
                    status="warning",
                    message="【高抽巷】层位须布置在煤层上方裂隙带内，距煤层顶板一般15~35m",
                    suggestion="施工前须进行钻孔验证层位,确保在裂隙带内有效抽采",
                ))
            # 低抽巷特殊要求
            if roadway == '低抽巷':
                items.append(ComplianceItem(
                    category="巷道类型", item="低抽巷底板控制",
                    status="warning",
                    message="【低抽巷】须布置在煤层底板，主要用于底板穿层钻孔预抽煤层瓦斯",
                    suggestion="钻孔间距应根据煤层透气性系数确定，突出煤层一般≤5m",
                ))

        # 回风巷 — 反风能力要求
        if roadway == '回风巷':
            items.append(ComplianceItem(
                category="巷道类型", item="回风巷反风系统",
                status="warning",
                message="【回风巷】须具备反风能力，反风量不得低于正常风量的40%",
                suggestion="检查主要通风机反风装置，制定反风演习计划",
            ))
            if inp.gas_level in ('高瓦斯', '突出'):
                items.append(ComplianceItem(
                    category="巷道类型", item="回风巷瓦斯监测",
                    status="warning",
                    message=f"【回风巷·{inp.gas_level}】回风流中须设置甲烷/风速传感器实时监控",
                    suggestion="传感器须按《煤矿安全规程》要求的位置和数量安装",
                ))

        # 切巷 — 短巷道特殊施工要求
        if roadway == '切巷':
            items.append(ComplianceItem(
                category="巷道类型", item="切巷贯通安全",
                status="warning",
                message="【切巷】属于贯通巷道，须编制贯通安全技术措施",
                suggestion="贯通前20m须停止一个工作面作业，做好通风系统调整方案",
            ))
            items.append(ComplianceItem(
                category="巷道类型", item="切巷顶板管理",
                status="warning",
                message="【切巷】宽度较大时须加强初次放顶和末采管理",
                suggestion="参照集团退锚放顶管理规定，制定安全技术措施",
            ))

        # ========== 6. 集团标准加严校核 ==========

        # 集团加严：最小净高（集团要求2.6m，国标2.5m）
        GROUP_MIN_HEIGHT = 2.6
        items.append(ComplianceItem(
            category="集团标准", item="最小净高",
            status="pass" if inp.section_height >= GROUP_MIN_HEIGHT else "fail",
            message=(
                f"【集团标准】净高 {inp.section_height}m "
                f"{'≥' if inp.section_height >= GROUP_MIN_HEIGHT else '<'} "
                f"集团要求 {GROUP_MIN_HEIGHT}m"
            ),
            suggestion="" if inp.section_height >= GROUP_MIN_HEIGHT else (
                f"集团标准要求净高不低于 {GROUP_MIN_HEIGHT}m"
            ),
        ))

        # 集团加严：最小净面积上浮10%
        group_min_area = min_area * 1.1
        items.append(ComplianceItem(
            category="集团标准", item="净断面积",
            status="pass" if area >= group_min_area else "warning",
            message=(
                f"【集团标准】净面积 {area:.1f}m² "
                f"{'≥' if area >= group_min_area else '<'} "
                f"集团要求 {group_min_area:.1f}m²（国标{min_area}m² × 1.1）"
            ),
            suggestion="" if area >= group_min_area else (
                f"建议增大断面至 {group_min_area:.1f}m² 以满足集团标准"
            ),
        ))

        # 集团要求：突出煤层必须编制防突专项措施
        if inp.gas_level == "突出":
            items.append(ComplianceItem(
                category="集团标准", item="防突专项措施",
                status="warning",
                message="【集团标准】突出煤层掘进须编制防突专项安全技术措施",
                suggestion="包含区域防突措施和局部防突措施，须经公司审批",
            ))

        # ========== 汇总 ==========
        n_pass = sum(1 for i in items if i.status == "pass")
        n_fail = sum(1 for i in items if i.status == "fail")
        n_warn = sum(1 for i in items if i.status == "warning")

        return ComplianceResult(
            total_checks=len(items),
            passed=n_pass,
            failed=n_fail,
            warned=n_warn,
            is_compliant=(n_fail == 0),
            items=items,
        )

    @staticmethod
    async def semantic_audit(
        chapters: list[dict],
        session,
        tenant_id: int = 0,
    ) -> list[ComplianceItem]:
        """
        语义级合规审查 — 用 RAG + LLM 对规程章节逐一与集团标准比对

        Args:
            chapters: [{"title": "...", "content": "..."}] 待审查的规程章节
            session: AsyncSession 数据库会话
            tenant_id: 租户ID

        Returns:
            合规差距项列表
        """
        from app.services.embedding_service import EmbeddingService
        from app.core.config import settings
        from openai import AsyncOpenAI

        items: list[ComplianceItem] = []
        emb_svc = EmbeddingService(session)

        api_key = settings.OPENAI_API_KEY or settings.GEMINI_API_KEY
        base_url = settings.OPENAI_BASE_URL or None
        model = settings.AI_MODEL

        if not api_key:
            return items  # 无大模型配置时降级

        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        client = AsyncOpenAI(**client_kwargs)

        for ch in chapters:
            # RAG 检索集团标准相关条款
            std_results = await emb_svc.search_similar(
                query=ch["title"], tenant_id=tenant_id, top_k=5, threshold=0.5
            )
            if not std_results:
                continue

            ref_text = "\n".join(
                f"- [{r['doc_title']}] {r['clause_no']}: {r['content'][:200]}"
                for r in std_results
            )

            prompt = (
                f"请对比以下规程章节内容与集团标准条款，列出不合规项（如有）。\n\n"
                f"【规程章节】{ch['title']}\n{ch['content'][:500]}\n\n"
                f"【集团标准参考条款】\n{ref_text}\n\n"
                f"输出格式：每项一行，格式为「❌/⚠️ [检查项]: 说明」。"
                f"如完全合规则输出「✅ 合规」。"
            )

            try:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                )
                audit_text = resp.choices[0].message.content or ""

                for line in audit_text.strip().splitlines():
                    line = line.strip()
                    if line.startswith("❌"):
                        items.append(ComplianceItem(
                            category="语义审查", item=ch["title"],
                            status="fail", message=line,
                            suggestion="请参照集团标准修改",
                        ))
                    elif line.startswith("⚠️"):
                        items.append(ComplianceItem(
                            category="语义审查", item=ch["title"],
                            status="warning", message=line,
                            suggestion="建议参照集团标准补充",
                        ))
            except Exception as e:
                print(f"⚠️ 语义审查失败({ch['title']}): {e}")

        return items
