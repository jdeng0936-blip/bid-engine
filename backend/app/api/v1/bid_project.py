"""
投标项目 API 路由 — BidProject + TenderRequirement + BidChapter CRUD
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user_payload, get_tenant_id
from app.schemas.common import ApiResponse
from app.schemas.bid_project import (
    BidProjectCreate, BidProjectUpdate, BidProjectOut, BidProjectListOut,
    TenderRequirementCreate, TenderRequirementUpdate, TenderRequirementOut,
    BidChapterCreate, BidChapterUpdate, BidChapterOut,
)
from app.services.bid_project_service import BidProjectService

router = APIRouter(prefix="/bid-projects", tags=["投标项目"])


# ========== BidProject CRUD ==========

@router.get("", response_model=ApiResponse[list[BidProjectListOut]])
async def list_projects(
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """获取投标项目列表"""
    svc = BidProjectService(session)
    items = await svc.list_projects(tenant_id)
    return ApiResponse(data=[BidProjectListOut.model_validate(p) for p in items])


@router.get("/{project_id}", response_model=ApiResponse[BidProjectOut])
async def get_project(
    project_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """获取投标项目详情（含招标要求和章节）"""
    svc = BidProjectService(session)
    project = await svc.get_project(project_id, tenant_id)
    if not project:
        raise HTTPException(status_code=404, detail="投标项目不存在")
    return ApiResponse(data=BidProjectOut.model_validate(project))


@router.post("", response_model=ApiResponse[BidProjectOut])
async def create_project(
    body: BidProjectCreate,
    tenant_id: int = Depends(get_tenant_id),
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """创建投标项目"""
    user_id = int(payload.get("sub", 0))
    svc = BidProjectService(session)
    project = await svc.create_project(body, tenant_id, user_id)
    return ApiResponse(data=BidProjectOut.model_validate(project))


@router.put("/{project_id}", response_model=ApiResponse[BidProjectOut])
async def update_project(
    project_id: int,
    body: BidProjectUpdate,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """更新投标项目"""
    svc = BidProjectService(session)
    project = await svc.update_project(project_id, tenant_id, body)
    if not project:
        raise HTTPException(status_code=404, detail="投标项目不存在")
    return ApiResponse(data=BidProjectOut.model_validate(project))


@router.delete("/{project_id}", response_model=ApiResponse)
async def delete_project(
    project_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """删除投标项目（级联删除关联数据）"""
    svc = BidProjectService(session)
    ok = await svc.delete_project(project_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="投标项目不存在")
    return ApiResponse(data={"deleted": True})


@router.patch("/{project_id}/status", response_model=ApiResponse[BidProjectOut])
async def update_status(
    project_id: int,
    status: str,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """更新投标项目状态"""
    svc = BidProjectService(session)
    project = await svc.update_status(project_id, tenant_id, status)
    if not project:
        raise HTTPException(status_code=404, detail="投标项目不存在")
    return ApiResponse(data=BidProjectOut.model_validate(project))


# ========== TenderRequirement CRUD ==========

@router.get("/{project_id}/requirements", response_model=ApiResponse[list[TenderRequirementOut]])
async def list_requirements(
    project_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """获取招标要求列表"""
    svc = BidProjectService(session)
    items = await svc.list_requirements(project_id, tenant_id)
    return ApiResponse(data=[TenderRequirementOut.model_validate(r) for r in items])


@router.post("/{project_id}/requirements", response_model=ApiResponse[TenderRequirementOut])
async def create_requirement(
    project_id: int,
    body: TenderRequirementCreate,
    tenant_id: int = Depends(get_tenant_id),
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """创建招标要求"""
    user_id = int(payload.get("sub", 0))
    svc = BidProjectService(session)
    req = await svc.create_requirement(project_id, tenant_id, body, user_id)
    if not req:
        raise HTTPException(status_code=404, detail="投标项目不存在")
    return ApiResponse(data=TenderRequirementOut.model_validate(req))


@router.post(
    "/{project_id}/requirements/batch",
    response_model=ApiResponse[list[TenderRequirementOut]],
)
async def batch_create_requirements(
    project_id: int,
    body: List[TenderRequirementCreate],
    tenant_id: int = Depends(get_tenant_id),
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """批量创建招标要求（招标文件解析后使用）"""
    user_id = int(payload.get("sub", 0))
    svc = BidProjectService(session)
    reqs = await svc.batch_create_requirements(project_id, tenant_id, body, user_id)
    return ApiResponse(data=[TenderRequirementOut.model_validate(r) for r in reqs])


@router.put("/requirements/{req_id}", response_model=ApiResponse[TenderRequirementOut])
async def update_requirement(
    req_id: int,
    body: TenderRequirementUpdate,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """更新招标要求"""
    svc = BidProjectService(session)
    req = await svc.update_requirement(req_id, tenant_id, body)
    if not req:
        raise HTTPException(status_code=404, detail="招标要求不存在")
    return ApiResponse(data=TenderRequirementOut.model_validate(req))


@router.delete("/requirements/{req_id}", response_model=ApiResponse)
async def delete_requirement(
    req_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """删除招标要求"""
    svc = BidProjectService(session)
    ok = await svc.delete_requirement(req_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="招标要求不存在")
    return ApiResponse(data={"deleted": True})


# ========== BidChapter CRUD ==========

@router.get("/{project_id}/chapters", response_model=ApiResponse[list[BidChapterOut]])
async def list_chapters(
    project_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """获取投标章节列表"""
    svc = BidProjectService(session)
    items = await svc.list_chapters(project_id, tenant_id)
    return ApiResponse(data=[BidChapterOut.model_validate(c) for c in items])


@router.post("/{project_id}/chapters", response_model=ApiResponse[BidChapterOut])
async def create_chapter(
    project_id: int,
    body: BidChapterCreate,
    tenant_id: int = Depends(get_tenant_id),
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """创建投标章节"""
    user_id = int(payload.get("sub", 0))
    svc = BidProjectService(session)
    chapter = await svc.create_chapter(project_id, tenant_id, body, user_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="投标项目不存在")
    return ApiResponse(data=BidChapterOut.model_validate(chapter))


@router.put("/chapters/{chapter_id}", response_model=ApiResponse[BidChapterOut])
async def update_chapter(
    chapter_id: int,
    body: BidChapterUpdate,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """更新投标章节"""
    svc = BidProjectService(session)
    chapter = await svc.update_chapter(chapter_id, tenant_id, body)
    if not chapter:
        raise HTTPException(status_code=404, detail="投标章节不存在")
    return ApiResponse(data=BidChapterOut.model_validate(chapter))


@router.delete("/chapters/{chapter_id}", response_model=ApiResponse)
async def delete_chapter(
    chapter_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """删除投标章节"""
    svc = BidProjectService(session)
    ok = await svc.delete_chapter(chapter_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="投标章节不存在")
    return ApiResponse(data={"deleted": True})
