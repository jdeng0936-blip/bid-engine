"""
支护计算引擎 — 无状态纯函数

核心公式来源：
  F1: 顶板锚杆锚固力 Q = K × γ × S × L (GB/T 35056)
  F2: 锚杆间排距验算 a ≤ L_f / (K × n)
  F3: 锚索破断力校核 P_b ≥ K_s × Q_单根
  F4: 巷道断面净面积 S = W×H (矩形) / π/8×W² (拱形)
  F5: 支护密度校核 N = S_top / (a × b)

合规拦截：若用户指定值不满足计算下限 → 红色预警。
"""
import math

from app.schemas.calc import SupportCalcInput, SupportCalcResult, CalcWarning


# 围岩级别 → 安全系数映射（国标基准）
ROCK_SAFETY_FACTOR: dict[str, float] = {
    "I": 1.2,
    "II": 1.3,
    "III": 1.5,
    "IV": 1.8,
    "V": 2.0,
}

# 围岩级别 → 推荐锚杆有效锚固长度系数
ROCK_ANCHOR_COEFFICIENT: dict[str, float] = {
    "I": 0.3,
    "II": 0.35,
    "III": 0.4,
    "IV": 0.45,
    "V": 0.5,
}

# ===== 集团加严参数（华阳集团《采掘运技术管理规定》）=====
# 集团加严：IV/V类围岩安全系数上调
GROUP_SAFETY_FACTOR_OVERRIDE: dict[str, float] = {
    "IV": 2.0,   # 国标1.8 → 集团2.0
    "V": 2.5,    # 国标2.0 → 集团2.5
}
# 集团加严：构造影响段间排距加密系数（缩小20%）
GROUP_STRUCT_ZONE_FACTOR: float = 0.8
# 集团要求：IV/V类围岩须全长锚固
GROUP_FULL_ANCHOR_ROCK_CLASSES: set[str] = {"IV", "V"}


class SupportCalcEngine:
    """支护计算引擎 — 无状态纯函数"""

    @staticmethod
    def calculate(input_data: SupportCalcInput) -> SupportCalcResult:
        """
        执行支护计算 + 合规校核

        Args:
            input_data: 支护计算输入参数

        Returns:
            SupportCalcResult 含计算结果和合规预警
        """
        warnings: list[CalcWarning] = []
        K_national = ROCK_SAFETY_FACTOR.get(input_data.rock_class, 1.5)
        # 集团加严：IV/V类围岩安全系数上调
        K = GROUP_SAFETY_FACTOR_OVERRIDE.get(input_data.rock_class, K_national)
        anchor_coeff = ROCK_ANCHOR_COEFFICIENT.get(input_data.rock_class, 0.4)

        W = input_data.section_width
        H = input_data.section_height
        gamma = input_data.rock_density  # t/m³
        L_bolt = input_data.bolt_length  # m
        d_bolt = input_data.bolt_diameter  # mm

        # ========== F4: 断面面积 ==========
        if input_data.section_form == "拱形":
            # 拱形：半圆拱 + 直墙，近似公式
            section_area = W * (H - W / 2) + math.pi * (W / 2) ** 2 / 2
        elif input_data.section_form == "梯形":
            # 梯形：按 0.9 系数修正
            section_area = W * H * 0.9
        else:
            # 矩形
            section_area = W * H

        # 顶板面积（按巷道宽度 × 1m 循环长度估算）
        S_top = W * 1.0  # m²/m（每米进尺的顶板面积）

        # ========== F1: 单根锚杆锚固力 ==========
        # Q = K × γ × 9.81 × S_影响面积 × L_bolt
        # 单根锚杆承担的影响面积初步按 0.8m×0.8m 估算
        influence_area = 0.64  # m²（保守取值）
        Q_bolt = K * gamma * 9.81 * influence_area * L_bolt  # kN
        bolt_force = round(Q_bolt, 2)

        # ========== F2: 最大锚杆间距/排距 ==========
        # 有效锚固长度
        L_f = L_bolt * anchor_coeff  # m
        # 锚杆抗拉承载力（按直径估算）
        # σ_t = 500 MPa (HRB500), A = π/4 × d²
        A_bolt = math.pi / 4 * (d_bolt / 1000) ** 2  # m²
        F_bolt = 500e3 * A_bolt  # kN (500 MPa)

        # 最大间距 = sqrt(F_bolt / (K × γ × 9.81 × L_bolt))
        max_spacing_m = math.sqrt(F_bolt / (K * gamma * 9.81 * L_bolt))
        max_bolt_spacing = round(min(max_spacing_m * 1000, 1000), 0)  # mm，上限 1000mm
        max_bolt_row_spacing = max_bolt_spacing  # 间排距相同

        # 推荐每排锚杆数
        recommended_per_row = max(math.ceil(W * 1000 / max_bolt_spacing), 3)

        # ========== F3: 锚索校核 ==========
        # 总支护载荷 = K × γ × 9.81 × S_top × L_bolt
        total_load = K * gamma * 9.81 * S_top * L_bolt
        total_support_load = round(total_load, 2)

        # 最少锚索数 = 总载荷 / (单根破断力 / K_s)
        K_s = 2.0  # 锚索安全系数
        cable_capacity = input_data.cable_strength / K_s
        min_cable = max(math.ceil(total_load / cable_capacity) if cable_capacity > 0 else 1, 1)

        # ========== F5: 支护密度 ==========
        if max_bolt_spacing > 0 and max_bolt_row_spacing > 0:
            density = 1e6 / (max_bolt_spacing * max_bolt_row_spacing)  # 根/m²
        else:
            density = 0
        support_density = round(density, 2)

        # ========== 安全系数 ==========
        safety_factor = round(K, 2)
        is_compliant = True

        # ========== 合规校核 ==========

        # 校核锚杆间距
        if input_data.bolt_spacing is not None:
            if input_data.bolt_spacing > max_bolt_spacing:
                warnings.append(CalcWarning(
                    level="error",
                    field="bolt_spacing",
                    message=(
                        f"锚杆间距超限：当前值 {input_data.bolt_spacing}mm "
                        f"> 最大允许值 {max_bolt_spacing}mm"
                    ),
                    current_value=input_data.bolt_spacing,
                    required_value=max_bolt_spacing,
                ))
                is_compliant = False

        # 校核锚杆排距
        if input_data.bolt_row_spacing is not None:
            if input_data.bolt_row_spacing > max_bolt_row_spacing:
                warnings.append(CalcWarning(
                    level="error",
                    field="bolt_row_spacing",
                    message=(
                        f"锚杆排距超限：当前值 {input_data.bolt_row_spacing}mm "
                        f"> 最大允许值 {max_bolt_row_spacing}mm"
                    ),
                    current_value=input_data.bolt_row_spacing,
                    required_value=max_bolt_row_spacing,
                ))
                is_compliant = False

        # 校核锚索数量
        if input_data.cable_count > 0 and input_data.cable_count < min_cable:
            warnings.append(CalcWarning(
                level="error",
                field="cable_count",
                message=(
                    f"锚索数量不足：当前 {input_data.cable_count} 根 "
                    f"< 最少要求 {min_cable} 根"
                ),
                current_value=float(input_data.cable_count),
                required_value=float(min_cable),
            ))
            is_compliant = False

        # 信息级提示
        if K >= 1.8:
            warnings.append(CalcWarning(
                level="warning",
                field="rock_class",
                message=f"{input_data.rock_class}类围岩条件差，建议加强支护监测",
                current_value=K,
                required_value=1.5,
            ))

        # ===== 集团标准合规校核 =====

        # 集团加严：IV/V类围岩安全系数上调提示
        if input_data.rock_class in GROUP_SAFETY_FACTOR_OVERRIDE:
            warnings.append(CalcWarning(
                level="info",
                field="safety_factor",
                message=(
                    f"【集团标准】{input_data.rock_class}类围岩安全系数已上调："
                    f"国标 {K_national} → 集团 {K}"
                ),
                current_value=K,
                required_value=K_national,
            ))

        # 集团要求：IV/V类围岩须全长锚固
        if input_data.rock_class in GROUP_FULL_ANCHOR_ROCK_CLASSES:
            warnings.append(CalcWarning(
                level="warning",
                field="anchor_type",
                message=(
                    f"【集团标准】{input_data.rock_class}类围岩必须采用全长锚固，"
                    f"严禁使用端头锚固"
                ),
                current_value=0,
                required_value=1,
            ))

        # 集团要求：锚杆预紧力纳入强制检查
        warnings.append(CalcWarning(
            level="info",
            field="pretension",
            message=(
                "【集团标准】锚杆预紧力必须逐根检查，"
                "锚索预应力必须全部达标，检测记录存档备查"
            ),
            current_value=0,
            required_value=1,
        ))

        # 集团要求：构造影响段提示
        warnings.append(CalcWarning(
            level="info",
            field="structural_zone",
            message=(
                f"【集团标准】过断层/陷落柱等构造影响段，间排距须缩小至 "
                f"{GROUP_STRUCT_ZONE_FACTOR*100:.0f}%，详见第三章“构造影响段加强支护”"
            ),
            current_value=1.0,
            required_value=GROUP_STRUCT_ZONE_FACTOR,
        ))

        return SupportCalcResult(
            section_area=round(section_area, 2),
            bolt_force=bolt_force,
            max_bolt_spacing=max_bolt_spacing,
            max_bolt_row_spacing=max_bolt_row_spacing,
            recommended_bolt_count_per_row=recommended_per_row,
            min_cable_count=min_cable,
            total_support_load=total_support_load,
            support_density=support_density,
            safety_factor=safety_factor,
            is_compliant=is_compliant,
            warnings=warnings,
        )
