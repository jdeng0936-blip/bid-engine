"""
投标复盘 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_tenant_id
from app.schemas.common import ApiResponse
from app.schemas.bid_review import BidReviewCreate, BidReviewUpdate, BidReviewOut
from app.services.bid_review_service import BidReviewService

router = APIRouter(prefix="/bid-projects/{project_id}/review", tags=["投标复盘"])


@router.get("", response_model=ApiResponse[BidReviewOut])
async def get_review(
    project_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    svc = BidReviewService(session)
    review = await svc.get_by_project(project_id, tenant_id)
    if not review:
        return ApiResponse(data=None)
    return ApiResponse(data=BidReviewOut.model_validate(review))


@router.post("", response_model=ApiResponse[BidReviewOut])
async def create_review(
    project_id: int,
    body: BidReviewCreate,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    svc = BidReviewService(session)
    existing = await svc.get_by_project(project_id, tenant_id)
    if existing:
        raise HTTPException(status_code=400, detail="该项目已有复盘记录，请使用 PUT 更新")
    review = await svc.create(project_id, tenant_id, body)
    return ApiResponse(data=BidReviewOut.model_validate(review))


@router.put("", response_model=ApiResponse[BidReviewOut])
async def update_review(
    project_id: int,
    body: BidReviewUpdate,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    svc = BidReviewService(session)
    review = await svc.update(project_id, tenant_id, body)
    if not review:
        raise HTTPException(status_code=404, detail="复盘记录不存在")
    return ApiResponse(data=BidReviewOut.model_validate(review))


@router.delete("", response_model=ApiResponse)
async def delete_review(
    project_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    svc = BidReviewService(session)
    ok = await svc.delete(project_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="复盘记录不存在")
    return ApiResponse(data={"deleted": True})
