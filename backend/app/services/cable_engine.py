"""
锚索受力计算引擎 — 无状态纯函数

核心公式:
  F1: 锚索悬吊力 Q_cable = K × γ × g × V_松动体
  F2: 松动圈高度 h = (0.2~0.5) × W（依围岩级别）
  F3: 单根锚索设计承载力 P_d = P_b / K_s
  F4: 最少锚索数 n = Q_total / P_d
  F5: 锚索预紧力校核 T_pre ≥ 0.4 × P_d
"""
import math
from pydantic import BaseModel, Field
from typing import Optional, Literal


# ========== Schema ==========

class CableCalcInput(BaseModel):
    """锚索受力计算输入"""
    rock_class: Literal["I", "II", "III", "IV", "V"] = Field(description="围岩级别")
    section_form: Literal["矩形", "拱形", "梯形"] = Field(description="断面形式")
    section_width: float = Field(gt=0, description="巷道净宽 m")
    section_height: float = Field(gt=0, description="巷道净高 m")
    rock_density: float = Field(default=2.5, gt=0, description="岩石容重 t/m³")
    cable_length: float = Field(default=6.3, gt=0, description="锚索长度 m")
    cable_diameter: float = Field(default=17.8, gt=0, description="锚索直径 mm")
    cable_strength: float = Field(default=353, gt=0, description="单根锚索极限破断力 kN")
    cable_count: Optional[int] = Field(default=None, ge=0, description="用户指定锚索数量（用于校核）")
    pretension: Optional[float] = Field(default=None, ge=0, description="用户指定预紧力 kN（用于校核）")
    row_spacing: float = Field(default=1600, gt=0, description="锚索排距 mm")


class CableWarning(BaseModel):
    """预警项"""
    level: Literal["error", "warning", "info"]
    field: str
    message: str
    current_value: float
    required_value: float


class CableCalcResult(BaseModel):
    """锚索受力计算结果"""
    loosening_height: float = Field(description="松动圈高度 m")
    loosening_volume: float = Field(description="松动体体积 m³/m")
    total_load: float = Field(description="总悬吊载荷 kN/m")
    design_capacity: float = Field(description="单根锚索设计承载力 kN")
    min_cable_count: int = Field(description="最少锚索数（每排）")
    recommended_spacing: float = Field(description="推荐锚索间距 mm")
    min_pretension: float = Field(description="最小预紧力 kN")
    safety_factor: float = Field(description="安全系数")
    is_compliant: bool = Field(description="是否合规")
    warnings: list[CableWarning] = Field(default_factory=list)


# ========== 常量 ==========

# 围岩级别 → 松动圈系数（松动圈高度 = 系数 × 巷宽）
LOOSENING_COEFF: dict[str, float] = {
    "I": 0.15, "II": 0.20, "III": 0.30, "IV": 0.40, "V": 0.50,
}

# 围岩级别 → 锚索安全系数
CABLE_SAFETY_FACTOR: dict[str, float] = {
    "I": 1.5, "II": 1.5, "III": 2.0, "IV": 2.0, "V": 2.5,
}


# ========== 计算引擎 ==========

class CableCalcEngine:
    """锚索受力计算引擎 — 无状态纯函数"""

    @staticmethod
    def calculate(inp: CableCalcInput) -> CableCalcResult:
        warnings: list[CableWarning] = []
        is_compliant = True

        W = inp.section_width
        H = inp.section_height
        gamma = inp.rock_density
        g = 9.81  # m/s²
        K_s = CABLE_SAFETY_FACTOR.get(inp.rock_class, 2.0)
        coeff = LOOSENING_COEFF.get(inp.rock_class, 0.3)

        # F2: 松动圈高度
        h = coeff * W  # m
        loosening_height = round(h, 2)

        # 松动体体积（每米进尺）
        # 矩形: V = W × h × 1
        # 拱形: V = (π/4 × W × h + W × h_rect) 近似
        if inp.section_form == "拱形":
            V = W * h * 1.1  # 拱形修正 +10%
        elif inp.section_form == "梯形":
            V = W * h * 0.95
        else:
            V = W * h * 1.0
        loosening_volume = round(V, 3)

        # F1: 总悬吊载荷（kN/m 进尺）
        Q_total = K_s * gamma * g * V
        total_load = round(Q_total, 2)

        # F3: 单根锚索设计承载力
        P_d = inp.cable_strength / K_s
        design_capacity = round(P_d, 2)

        # F4: 最少锚索数（每排）
        min_n = max(math.ceil(Q_total / P_d), 1)

        # 推荐间距
        if min_n > 1:
            rec_spacing = round(W * 1000 / (min_n + 1), 0)  # mm
        else:
            rec_spacing = round(W * 1000 / 2, 0)

        # F5: 最小预紧力（≥ 40% 设计承载力）
        T_pre_min = round(0.4 * P_d, 2)

        # ========== 合规校核 ==========

        # 校核用户指定锚索数
        if inp.cable_count is not None and inp.cable_count > 0:
            if inp.cable_count < min_n:
                warnings.append(CableWarning(
                    level="error", field="cable_count",
                    message=f"锚索数量不足：当前 {inp.cable_count} 根 < 最少 {min_n} 根",
                    current_value=float(inp.cable_count),
                    required_value=float(min_n),
                ))
                is_compliant = False

        # 校核预紧力
        if inp.pretension is not None:
            if inp.pretension < T_pre_min:
                warnings.append(CableWarning(
                    level="error", field="pretension",
                    message=f"预紧力不足：当前 {inp.pretension} kN < 最小 {T_pre_min} kN",
                    current_value=inp.pretension,
                    required_value=T_pre_min,
                ))
                is_compliant = False

        # 围岩级别提示
        if K_s >= 2.0:
            warnings.append(CableWarning(
                level="warning", field="rock_class",
                message=f"{inp.rock_class}类围岩松动圈大（{loosening_height}m），建议锚索深入稳定岩层 ≥1.5m",
                current_value=K_s, required_value=1.5,
            ))

        return CableCalcResult(
            loosening_height=loosening_height,
            loosening_volume=loosening_volume,
            total_load=total_load,
            design_capacity=design_capacity,
            min_cable_count=min_n,
            recommended_spacing=rec_spacing,
            min_pretension=T_pre_min,
            safety_factor=round(K_s, 2),
            is_compliant=is_compliant,
            warnings=warnings,
        )
