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
