"""
FastAPI 依赖注入 — 当前用户 + tenant_id 隔离
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import decode_access_token

# Bearer Token 自动提取
bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user_payload(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """从 JWT 中提取用户信息和 tenant_id

    所有需要认证的 API 都应依赖此函数。
    返回 payload dict，至少包含 sub(user_id)、tenant_id。
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 中缺少用户标识",
        )
    return payload


async def get_tenant_id(
    payload: dict = Depends(get_current_user_payload),
) -> int:
    """提取当前请求的 tenant_id（企业/租户 ID）

    规范红线：所有关系查询必须注入 tenant_id 过滤。
    """
    tenant_id = payload.get("tenant_id")
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="缺少租户标识，拒绝访问",
        )
    return int(tenant_id)
