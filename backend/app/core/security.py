"""
安全模块 — JWT 签发/验证 + 密码哈希
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from jose import JWTError, jwt
import bcrypt as _bcrypt

from app.core.config import settings

# JWT 常量
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希"""
    return _bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    """生成 bcrypt 哈希"""
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def create_access_token(
    subject: Any,
    tenant_id: Optional[int] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """签发 JWT Access Token

    payload 中注入 tenant_id 用于权限隔离
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "sub": str(subject),
        "exp": expire,
    }
    if tenant_id is not None:
        to_encode["tenant_id"] = tenant_id
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """解码并验证 JWT Token

    Raises:
        JWTError: Token 无效或已过期
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


# ============================================================
# RBAC 权限控制 — 基于角色的 API 访问控制
# ============================================================

from functools import wraps
from fastapi import Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


async def get_current_user(
    payload: dict = None,
    session: "AsyncSession" = None,
):
    """
    从 JWT payload + DB 查询获取完整用户对象（含角色）
    注意：此函数需要通过 Depends 注入 payload 和 session，
    在实际使用中通过 get_current_user_dep 获取。
    """
    from app.core.deps import get_current_user_payload
    from app.core.database import get_async_session
    from app.models.user import SysUser

    user_id = int(payload["sub"])
    result = await session.execute(
        select(SysUser).where(SysUser.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )
    return user


def require_role(*allowed_roles: str):
    """RBAC 权限装饰器 — 限制 API 只允许指定角色访问

    用法:
        @router.get("/admin-only")
        @require_role("管理员")
        async def admin_endpoint(...):

    或允许多角色:
        @require_role("管理员", "审核员")

    实现原理:
        1. 从 JWT 中提取 user_id
        2. 查询数据库获取用户角色
        3. 校验角色是否在允许列表中
    """
    from app.core.deps import get_current_user_payload
    from app.core.database import get_async_session
    from app.models.user import SysUser

    async def role_checker(
        payload: dict = Depends(get_current_user_payload),
        session: AsyncSession = Depends(get_async_session),
    ) -> SysUser:
        """依赖注入函数 — 校验用户角色"""
        user_id = int(payload["sub"])
        result = await session.execute(
            select(SysUser).where(SysUser.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已被禁用",
            )

        # 获取角色名称
        role_name = user.role.name if user.role else None
        if role_name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要角色: {', '.join(allowed_roles)}",
            )
        return user

    return Depends(role_checker)

