"""
报价表 Schema — Pydantic V2

覆盖：QuotationSheet / QuotationItem CRUD
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ========== QuotationItem ==========

class QuotationItemCreate(BaseModel):
    """创建报价明细"""
    category: str = Field(description="品类: vegetable/meat/seafood/egg_poultry/dry_goods/condiment")
    item_name: str = Field(min_length=1, max_length=100, description="品名")
    spec: Optional[str] = Field(None, max_length=100, description="规格")
    unit: Optional[str] = Field(None, max_length=20, description="单位")
    market_ref_price: Optional[float] = Field(None, description="市场参考价（元）")
    unit_price: Optional[float] = Field(None, description="投标单价（元）")
    quantity: Optional[float] = Field(None, description="预计采购量")
    amount: Optional[float] = Field(None, description="小计金额（元）")
    sort_order: int = Field(0, description="排序号")


class QuotationItemUpdate(BaseModel):
    """更新报价明细"""
    category: Optional[str] = None
    item_name: Optional[str] = Field(None, max_length=100)
    spec: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=20)
    market_ref_price: Optional[float] = None
    unit_price: Optional[float] = None
    quantity: Optional[float] = None
    amount: Optional[float] = None
    sort_order: Optional[int] = None


class QuotationItemOut(BaseModel):
    """报价明细输出"""
    id: int
    sheet_id: int
    category: str
    item_name: str
    spec: Optional[str] = None
    unit: Optional[str] = None
    market_ref_price: Optional[float] = None
    unit_price: Optional[float] = None
    quantity: Optional[float] = None
    amount: Optional[float] = None
    sort_order: int = 0

    model_config = ConfigDict(from_attributes=True)


# ========== QuotationSheet ==========

class QuotationSheetCreate(BaseModel):
    """创建报价表"""
    project_id: int = Field(description="投标项目ID")
    discount_rate: Optional[float] = Field(None, description="下浮率（如0.08代表下浮8%）")
    budget_amount: Optional[float] = Field(None, description="预算金额（元）")
    pricing_method: Optional[str] = Field(None, description="报价方式: fixed_price/discount_rate/comprehensive")
    remarks: Optional[str] = Field(None, description="报价说明")
    items: List[QuotationItemCreate] = Field(default_factory=list, description="报价明细行")


class QuotationSheetUpdate(BaseModel):
    """更新报价表"""
    discount_rate: Optional[float] = None
    total_amount: Optional[float] = None
    budget_amount: Optional[float] = None
    pricing_method: Optional[str] = None
    remarks: Optional[str] = None


class QuotationSheetOut(BaseModel):
    """报价表输出"""
    id: int
    project_id: int
    version: int = 1
    discount_rate: Optional[float] = None
    total_amount: Optional[float] = None
    budget_amount: Optional[float] = None
    pricing_method: Optional[str] = None
    remarks: Optional[str] = None
    items: List[QuotationItemOut] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
