"""
认证相关 Schema — Pydantic V2
"""
from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """注册请求 — 新用户注册同时创建租户"""
    username: str
    password: str
    confirm_password: str
    real_name: str = ""
    enterprise_name: str = ""  # 企业名称，注册时自动创建租户


class TokenResponse(BaseModel):
    """登录成功返回 Token"""
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    """当前用户信息"""
    id: int
    username: str
    real_name: Optional[str] = None
    role_name: Optional[str] = None
    tenant_id: int

    model_config = {"from_attributes": True}
