"""
标准库 API 路由 — 规范文档 CRUD + 条款树管理

所有接口强制 JWT 认证 + tenant_id 隔离。
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user_payload, get_tenant_id
from app.schemas.common import ApiResponse, PaginatedData
from app.schemas.standard import (
    StdDocumentCreate,
    StdDocumentUpdate,
    StdDocumentOut,
    StdClauseCreate,
    StdClauseUpdate,
    StdClauseOut,
    StdClauseTree,
)
from app.services.standard_service import StandardService

router = APIRouter(prefix="/standards", tags=["标准库"])


# ========== 规范文档 ==========

@router.get("", response_model=ApiResponse[PaginatedData[StdDocumentOut]])
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    doc_type: Optional[str] = Query(None, description="文档类型筛选"),
    title: Optional[str] = Query(None, description="标题模糊搜索"),
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """获取规范文档列表（分页 + 筛选）"""
    svc = StandardService(session)
    items, total = await svc.list_documents(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        doc_type=doc_type,
        title=title,
    )
    return ApiResponse(
        data=PaginatedData(
            items=items, total=total, page=page, page_size=page_size
        )
    )


@router.post("", response_model=ApiResponse[StdDocumentOut])
async def create_document(
    body: StdDocumentCreate,
    payload: dict = Depends(get_current_user_payload),
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """新建规范文档"""
    svc = StandardService(session)
    doc = await svc.create_document(
        data=body,
        tenant_id=tenant_id,
        created_by=int(payload["sub"]),
    )
    return ApiResponse(data=StdDocumentOut.model_validate(doc))


@router.get("/{doc_id}", response_model=ApiResponse)
async def get_document(
    doc_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """获取文档详情（含条款树）"""
    svc = StandardService(session)
    doc = await svc.get_document(doc_id, tenant_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    clause_tree = await svc.get_clause_tree(doc_id)
    return ApiResponse(data={
        "document": StdDocumentOut.model_validate(doc).model_dump(),
        "clauses": [c.model_dump() for c in clause_tree],
    })


@router.put("/{doc_id}", response_model=ApiResponse[StdDocumentOut])
async def update_document(
    doc_id: int,
    body: StdDocumentUpdate,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """更新文档基础信息"""
    svc = StandardService(session)
    doc = await svc.update_document(doc_id, tenant_id, body)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return ApiResponse(data=StdDocumentOut.model_validate(doc))


@router.delete("/{doc_id}", response_model=ApiResponse)
async def delete_document(
    doc_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """删除文档（级联删除所有条款）"""
    svc = StandardService(session)
    success = await svc.delete_document(doc_id, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    return ApiResponse(message="删除成功")


# ========== 条款管理 ==========

@router.get("/{doc_id}/clauses", response_model=ApiResponse[list[StdClauseTree]])
async def get_clause_tree(
    doc_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """获取文档的条款树"""
    svc = StandardService(session)
    # 先验证文档归属
    doc = await svc.get_document(doc_id, tenant_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    tree = await svc.get_clause_tree(doc_id)
    return ApiResponse(data=tree)


@router.post("/{doc_id}/clauses", response_model=ApiResponse[StdClauseOut])
async def create_clause(
    doc_id: int,
    body: StdClauseCreate,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """新增条款"""
    svc = StandardService(session)
    doc = await svc.get_document(doc_id, tenant_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    clause = await svc.create_clause(doc_id, body)
    return ApiResponse(data=StdClauseOut.model_validate(clause))


@router.put("/clauses/{clause_id}", response_model=ApiResponse[StdClauseOut])
async def update_clause(
    clause_id: int,
    body: StdClauseUpdate,
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """更新条款"""
    svc = StandardService(session)
    clause = await svc.update_clause(clause_id, body)
    if not clause:
        raise HTTPException(status_code=404, detail="条款不存在")
    return ApiResponse(data=StdClauseOut.model_validate(clause))


@router.delete("/clauses/{clause_id}", response_model=ApiResponse)
async def delete_clause(
    clause_id: int,
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """删除条款（递归删除子条款）"""
    svc = StandardService(session)
    success = await svc.delete_clause(clause_id)
    if not success:
        raise HTTPException(status_code=404, detail="条款不存在")
    return ApiResponse(message="删除成功")
