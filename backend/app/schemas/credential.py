"""
资质证书 Schema — Pydantic V2

覆盖：Credential CRUD + 到期预警
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CredentialCreate(BaseModel):
    """创建资质证书"""
    enterprise_id: int = Field(description="所属企业ID")
    cred_type: str = Field(max_length=50, description="证书类型（见 CredentialType 枚举）")
    cred_name: str = Field(min_length=1, max_length=200, description="证书名称")
    cred_no: Optional[str] = Field(None, max_length=100, description="证书编号")
    issue_date: Optional[str] = Field(None, max_length=20, description="发证日期")
    expiry_date: Optional[str] = Field(None, max_length=20, description="到期日期")
    is_permanent: bool = Field(False, description="是否长期有效")
    issuing_authority: Optional[str] = Field(None, max_length=200, description="发证机关")
    file_path: Optional[str] = Field(None, description="扫描件路径")
    file_name: Optional[str] = Field(None, max_length=200, description="原始文件名")
    is_verified: bool = Field(False, description="是否已验证")
    remarks: Optional[str] = Field(None, description="备注")


class CredentialUpdate(BaseModel):
    """更新资质证书"""
    cred_type: Optional[str] = Field(None, max_length=50)
    cred_name: Optional[str] = Field(None, max_length=200)
    cred_no: Optional[str] = Field(None, max_length=100)
    issue_date: Optional[str] = Field(None, max_length=20)
    expiry_date: Optional[str] = Field(None, max_length=20)
    is_permanent: Optional[bool] = None
    issuing_authority: Optional[str] = Field(None, max_length=200)
    file_path: Optional[str] = None
    file_name: Optional[str] = Field(None, max_length=200)
    is_verified: Optional[bool] = None
    remarks: Optional[str] = None


class CredentialOut(BaseModel):
    """资质证书输出"""
    id: int
    tenant_id: int
    enterprise_id: int
    cred_type: str
    cred_name: str
    cred_no: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    is_permanent: bool = False
    issuing_authority: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    is_verified: bool = False
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
