"""
图片资源库 API 路由 — ImageAsset CRUD
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user_payload, get_tenant_id
from app.schemas.common import ApiResponse
from app.schemas.image_asset import ImageAssetCreate, ImageAssetUpdate, ImageAssetOut
from app.services.image_asset_service import ImageAssetService

router = APIRouter(prefix="/images", tags=["图片资源库"])


@router.get("/enterprise/{enterprise_id}", response_model=ApiResponse[list[ImageAssetOut]])
async def list_images(
    enterprise_id: int,
    category: Optional[str] = Query(None, description="按分类筛选"),
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """获取企业的图片资源列表"""
    svc = ImageAssetService(session)
    items = await svc.list_by_enterprise(enterprise_id, tenant_id, category)
    return ApiResponse(data=[ImageAssetOut.model_validate(i) for i in items])


@router.get("/enterprise/{enterprise_id}/defaults", response_model=ApiResponse[list[ImageAssetOut]])
async def get_default_images(
    enterprise_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """获取每个分类的默认图片（AI文档生成时使用）"""
    svc = ImageAssetService(session)
    items = await svc.get_defaults_by_category(enterprise_id, tenant_id)
    return ApiResponse(data=[ImageAssetOut.model_validate(i) for i in items])


@router.get("/{image_id}", response_model=ApiResponse[ImageAssetOut])
async def get_image(
    image_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """获取图片资源详情"""
    svc = ImageAssetService(session)
    image = await svc.get_image(image_id, tenant_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片资源不存在")
    return ApiResponse(data=ImageAssetOut.model_validate(image))


@router.post("", response_model=ApiResponse[ImageAssetOut])
async def create_image(
    body: ImageAssetCreate,
    tenant_id: int = Depends(get_tenant_id),
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """创建图片资源记录"""
    user_id = int(payload.get("sub", 0))
    svc = ImageAssetService(session)
    image = await svc.create_image(body, tenant_id, user_id)
    return ApiResponse(data=ImageAssetOut.model_validate(image))


@router.put("/{image_id}", response_model=ApiResponse[ImageAssetOut])
async def update_image(
    image_id: int,
    body: ImageAssetUpdate,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """更新图片资源"""
    svc = ImageAssetService(session)
    image = await svc.update_image(image_id, tenant_id, body)
    if not image:
        raise HTTPException(status_code=404, detail="图片资源不存在")
    return ApiResponse(data=ImageAssetOut.model_validate(image))


@router.delete("/{image_id}", response_model=ApiResponse)
async def delete_image(
    image_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """删除图片资源"""
    svc = ImageAssetService(session)
    ok = await svc.delete_image(image_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="图片资源不存在")
    return ApiResponse(data={"deleted": True})
