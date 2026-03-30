"""
企业信息 Schema — Pydantic V2

覆盖：Enterprise CRUD
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ========== Enterprise ==========

class EnterpriseCreate(BaseModel):
    """创建企业"""
    name: str = Field(min_length=1, max_length=200, description="企业名称")
    short_name: Optional[str] = Field(None, max_length=50, description="企业简称")
    credit_code: Optional[str] = Field(None, max_length=50, description="统一社会信用代码")
    legal_representative: Optional[str] = Field(None, max_length=50, description="法定代表人")
    registered_capital: Optional[str] = Field(None, max_length=50, description="注册资本（万元）")
    established_date: Optional[str] = Field(None, max_length=20, description="成立日期")
    business_scope: Optional[str] = Field(None, description="经营范围")

    # 食品行业专属
    food_license_no: Optional[str] = Field(None, max_length=100, description="食品经营许可证号")
    food_license_expiry: Optional[str] = Field(None, max_length=20, description="食品经营许可证到期日")
    haccp_certified: bool = Field(False, description="是否通过HACCP认证")
    iso22000_certified: bool = Field(False, description="是否通过ISO22000认证")
    sc_certified: bool = Field(False, description="是否有SC认证")

    # 冷链资产
    cold_chain_vehicles: int = Field(0, description="冷链车辆数")
    normal_vehicles: int = Field(0, description="常温车辆数")
    warehouse_area: Optional[float] = Field(None, description="仓储面积（㎡）")
    cold_storage_area: Optional[float] = Field(None, description="冷库面积（㎡）")
    cold_storage_temp: Optional[str] = Field(None, max_length=50, description="冷库温度范围")

    # 联系信息
    address: Optional[str] = Field(None, description="公司地址")
    contact_person: Optional[str] = Field(None, max_length=50, description="联系人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    contact_email: Optional[str] = Field(None, max_length=100, description="邮箱")

    # 经营数据
    employee_count: Optional[int] = Field(None, description="员工人数")
    annual_revenue: Optional[str] = Field(None, max_length=50, description="年营收（万元）")
    service_customers: Optional[int] = Field(None, description="服务客户数")

    # 简介
    description: Optional[str] = Field(None, description="企业简介")
    competitive_advantages: Optional[str] = Field(None, description="核心竞争优势")


class EnterpriseUpdate(BaseModel):
    """更新企业"""
    name: Optional[str] = Field(None, max_length=200)
    short_name: Optional[str] = Field(None, max_length=50)
    credit_code: Optional[str] = Field(None, max_length=50)
    legal_representative: Optional[str] = Field(None, max_length=50)
    registered_capital: Optional[str] = Field(None, max_length=50)
    established_date: Optional[str] = Field(None, max_length=20)
    business_scope: Optional[str] = None

    food_license_no: Optional[str] = Field(None, max_length=100)
    food_license_expiry: Optional[str] = Field(None, max_length=20)
    haccp_certified: Optional[bool] = None
    iso22000_certified: Optional[bool] = None
    sc_certified: Optional[bool] = None

    cold_chain_vehicles: Optional[int] = None
    normal_vehicles: Optional[int] = None
    warehouse_area: Optional[float] = None
    cold_storage_area: Optional[float] = None
    cold_storage_temp: Optional[str] = Field(None, max_length=50)

    address: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=50)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=100)

    employee_count: Optional[int] = None
    annual_revenue: Optional[str] = Field(None, max_length=50)
    service_customers: Optional[int] = None

    description: Optional[str] = None
    competitive_advantages: Optional[str] = None


class EnterpriseOut(BaseModel):
    """企业输出"""
    id: int
    tenant_id: int
    name: str
    short_name: Optional[str] = None
    credit_code: Optional[str] = None
    legal_representative: Optional[str] = None
    registered_capital: Optional[str] = None
    established_date: Optional[str] = None
    business_scope: Optional[str] = None

    food_license_no: Optional[str] = None
    food_license_expiry: Optional[str] = None
    haccp_certified: bool = False
    iso22000_certified: bool = False
    sc_certified: bool = False

    cold_chain_vehicles: int = 0
    normal_vehicles: int = 0
    warehouse_area: Optional[float] = None
    cold_storage_area: Optional[float] = None
    cold_storage_temp: Optional[str] = None

    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None

    employee_count: Optional[int] = None
    annual_revenue: Optional[str] = None
    service_customers: Optional[int] = None

    description: Optional[str] = None
    competitive_advantages: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
