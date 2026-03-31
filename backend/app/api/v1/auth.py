"""
认证路由 — 登录 / 登出 / 当前用户
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_async_session
from app.core.security import verify_password, create_access_token
from app.core.deps import get_current_user_payload
from app.models.user import SysUser
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserProfile
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """用户登录，返回 JWT Token"""
    result = await session.execute(
        select(SysUser).where(SysUser.username == body.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )

    token = create_access_token(
        subject=user.id,
        tenant_id=user.tenant_id,
    )
    return ApiResponse(data=TokenResponse(access_token=token))


@router.get("/profile", response_model=ApiResponse[UserProfile])
async def get_profile(
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """获取当前登录用户信息"""
    user_id = int(payload["sub"])
    result = await session.execute(
        select(SysUser).where(SysUser.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return ApiResponse(
        data=UserProfile(
            id=user.id,
            username=user.username,
            real_name=user.real_name,
            role_name=user.role.name if user.role else None,
            tenant_id=user.tenant_id,
        )
    )


@router.post("/register", response_model=ApiResponse[TokenResponse])
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """用户注册 — 新用户注册同时自动创建租户

    业务流程:
      1. 校验密码一致性 + 用户名唯一性
      2. 创建租户（tenant_id 以 sys_user.id 为准，自增）
      3. 创建默认角色（普通用户）
      4. 创建用户
      5. 返回 JWT Token（注册即登录）
    """
    from app.schemas.auth import RegisterRequest as RegReq
    from app.core.security import get_password_hash

    # 1. 密码一致性校验
    if body.password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="两次密码输入不一致",
        )
    if len(body.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度不能少于6位",
        )

    # 2. 用户名唯一性校验
    existing = await session.execute(
        select(SysUser).where(SysUser.username == body.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已被注册",
        )

    # 3. 创建角色（普通用户角色，per-tenant）
    from app.models.user import SysRole

    # 先获取最大tenant_id，新租户ID = max + 1
    max_tenant_result = await session.execute(
        select(func.max(SysUser.tenant_id))
    )
    max_tenant = max_tenant_result.scalar() or 0
    new_tenant_id = max_tenant + 1

    user_role = SysRole(
        name="普通用户",
        description="投标项目管理",
        tenant_id=new_tenant_id,
        created_by=0,
    )
    session.add(user_role)
    await session.flush()  # 获取 role.id

    # 4. 创建用户
    new_user = SysUser(
        username=body.username,
        hashed_password=get_password_hash(body.password),
        real_name=body.real_name or body.username,
        role_id=user_role.id,
        is_active=True,
        tenant_id=new_tenant_id,
        created_by=0,
    )
    session.add(new_user)
    await session.flush()  # 获取 user.id

    # 5. 如果提供了企业名称，自动创建企业
    if body.enterprise_name.strip():
        from app.models.enterprise import Enterprise
        enterprise = Enterprise(
            name=body.enterprise_name.strip(),
            tenant_id=new_tenant_id,
            created_by=new_user.id,
        )
        session.add(enterprise)

    await session.commit()

    # 6. 签发 Token（注册即登录）
    token = create_access_token(
        subject=new_user.id,
        tenant_id=new_tenant_id,
    )
    return ApiResponse(data=TokenResponse(access_token=token))
