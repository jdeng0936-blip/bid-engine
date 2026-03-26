"""
设备材料配置模块 — Pydantic V2 Schema

请求/响应模型，用于 API 接口校验。
"""
from typing import Optional
from pydantic import BaseModel, Field


# ===================== 设备目录 =====================

class EquipmentCatalogItem(BaseModel):
    """设备目录条目"""
    id: int
    name: str
    category: str
    model_spec: Optional[str] = None
    manufacturer: Optional[str] = None
    power_kw: Optional[float] = None
    weight_t: Optional[float] = None
    tech_params: Optional[dict] = None
    applicable_conditions: Optional[str] = None

    model_config = {"from_attributes": True}


class EquipmentCatalogCreate(BaseModel):
    """新建设备目录条目"""
    name: str = Field(..., max_length=100, description="设备名称")
    category: str = Field(..., max_length=30, description="设备类别")
    model_spec: Optional[str] = Field(None, max_length=100, description="型号规格")
    manufacturer: Optional[str] = Field(None, max_length=100, description="生产厂家")
    power_kw: Optional[float] = Field(None, description="额定功率(kW)")
    weight_t: Optional[float] = Field(None, description="设备重量(t)")
    tech_params: Optional[dict] = Field(None, description="主要技术参数(JSON)")
    applicable_conditions: Optional[str] = Field(None, description="适用条件描述")
    match_dig_methods: Optional[str] = Field(None, description="适用掘进方式(逗号分隔)")
    match_excavation_types: Optional[str] = Field(None, description="适用掘进类型(逗号分隔)")
    match_min_section_area: Optional[float] = Field(None, description="适用最小断面面积")
    match_max_section_area: Optional[float] = Field(None, description="适用最大断面面积")


# ===================== 材料目录 =====================

class MaterialCatalogItem(BaseModel):
    """材料目录条目"""
    id: int
    name: str
    category: str
    model_spec: Optional[str] = None
    unit: str
    consumption_per_cycle: Optional[float] = None
    tech_params: Optional[dict] = None

    model_config = {"from_attributes": True}


class MaterialCatalogCreate(BaseModel):
    """新建材料目录条目"""
    name: str = Field(..., max_length=100, description="材料名称")
    category: str = Field(..., max_length=30, description="材料类别")
    model_spec: Optional[str] = Field(None, max_length=100, description="规格型号")
    unit: str = Field("根", max_length=10, description="计量单位")
    consumption_per_cycle: Optional[float] = Field(None, description="单循环消耗量(基准值)")
    match_support_types: Optional[str] = Field(None, description="适用支护方式(逗号分隔)")
    match_rock_classes: Optional[str] = Field(None, description="适用围岩级别(逗号分隔)")
    tech_params: Optional[dict] = Field(None, description="技术参数(JSON)")


# ===================== 项目设备清单 =====================

class ProjectEquipmentItem(BaseModel):
    """项目设备清单条目"""
    id: int
    project_id: int
    name: str
    category: str
    model_spec: Optional[str] = None
    quantity: int = 1
    power_kw: Optional[float] = None
    tech_params_summary: Optional[str] = None
    match_source: str = "auto"

    model_config = {"from_attributes": True}


# ===================== 项目材料 BOM =====================

class ProjectMaterialBomItem(BaseModel):
    """项目材料工程量清单条目"""
    id: int
    project_id: int
    name: str
    category: str
    model_spec: Optional[str] = None
    unit: str
    qty_per_cycle: Optional[float] = None
    qty_per_month: Optional[float] = None
    qty_total: Optional[float] = None
    calc_basis: Optional[str] = None
    match_source: str = "auto"

    model_config = {"from_attributes": True}


# ===================== 匹配请求/结果 =====================

class EquipmentMatchRequest(BaseModel):
    """设备材料匹配请求 — 可由项目参数自动提取，也可前端手动传入"""
    project_id: int = Field(..., description="项目ID")


class EquipmentMatchResult(BaseModel):
    """设备材料匹配结果"""
    project_id: int
    equipment_list: list[ProjectEquipmentItem] = []
    material_bom: list[ProjectMaterialBomItem] = []
    total_equipment_count: int = 0
    total_material_types: int = 0
