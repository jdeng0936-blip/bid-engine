"""
资质证书 API 路由 — Credential CRUD + 到期预警
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user_payload, get_tenant_id
from app.schemas.common import ApiResponse
from app.schemas.credential import CredentialCreate, CredentialUpdate, CredentialOut
from app.services.credential_service import CredentialService

router = APIRouter(prefix="/credentials", tags=["资质证书"])


@router.get("/enterprise/{enterprise_id}", response_model=ApiResponse[list[CredentialOut]])
async def list_credentials(
    enterprise_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """获取企业的资质证书列表"""
    svc = CredentialService(session)
    items = await svc.list_by_enterprise(enterprise_id, tenant_id)
    return ApiResponse(data=[CredentialOut.model_validate(c) for c in items])


@router.get("/expiring", response_model=ApiResponse[list[CredentialOut]])
async def get_expiring(
    days: Optional[int] = Query(None, description="预警天数（默认读取配置）"),
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """获取即将到期的资质证书"""
    svc = CredentialService(session)
    items = await svc.get_expiring_credentials(tenant_id, days)
    return ApiResponse(data=[CredentialOut.model_validate(c) for c in items])


@router.get("/{cred_id}", response_model=ApiResponse[CredentialOut])
async def get_credential(
    cred_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """获取资质证书详情"""
    svc = CredentialService(session)
    cred = await svc.get_credential(cred_id, tenant_id)
    if not cred:
        raise HTTPException(status_code=404, detail="资质证书不存在")
    return ApiResponse(data=CredentialOut.model_validate(cred))


@router.post("", response_model=ApiResponse[CredentialOut])
async def create_credential(
    body: CredentialCreate,
    tenant_id: int = Depends(get_tenant_id),
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """创建资质证书"""
    user_id = int(payload.get("sub", 0))
    svc = CredentialService(session)
    cred = await svc.create_credential(body, tenant_id, user_id)
    return ApiResponse(data=CredentialOut.model_validate(cred))


@router.put("/{cred_id}", response_model=ApiResponse[CredentialOut])
async def update_credential(
    cred_id: int,
    body: CredentialUpdate,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """更新资质证书"""
    svc = CredentialService(session)
    cred = await svc.update_credential(cred_id, tenant_id, body)
    if not cred:
        raise HTTPException(status_code=404, detail="资质证书不存在")
    return ApiResponse(data=CredentialOut.model_validate(cred))


@router.delete("/{cred_id}", response_model=ApiResponse)
async def delete_credential(
    cred_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """删除资质证书"""
    svc = CredentialService(session)
    ok = await svc.delete_credential(cred_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="资质证书不存在")
    return ApiResponse(data={"deleted": True})
