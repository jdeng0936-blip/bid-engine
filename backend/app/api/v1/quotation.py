"""
报价表 API 路由 — QuotationSheet + QuotationItem CRUD
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user_payload, get_tenant_id
from app.schemas.common import ApiResponse
from app.schemas.quotation import (
    QuotationSheetCreate, QuotationSheetUpdate, QuotationSheetOut,
    QuotationItemCreate, QuotationItemUpdate, QuotationItemOut,
)
from app.services.quotation_service import QuotationService

router = APIRouter(prefix="/quotations", tags=["报价管理"])


# ========== QuotationSheet ==========

@router.get("/project/{project_id}", response_model=ApiResponse[list[QuotationSheetOut]])
async def list_sheets(
    project_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """获取投标项目的报价表列表"""
    svc = QuotationService(session)
    items = await svc.list_sheets(project_id, tenant_id)
    return ApiResponse(data=[QuotationSheetOut.model_validate(s) for s in items])


@router.get("/{sheet_id}", response_model=ApiResponse[QuotationSheetOut])
async def get_sheet(
    sheet_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """获取报价表详情（含明细行）"""
    svc = QuotationService(session)
    sheet = await svc.get_sheet(sheet_id, tenant_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="报价表不存在")
    return ApiResponse(data=QuotationSheetOut.model_validate(sheet))


@router.post("", response_model=ApiResponse[QuotationSheetOut])
async def create_sheet(
    body: QuotationSheetCreate,
    tenant_id: int = Depends(get_tenant_id),
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """创建报价表（可附带明细行）"""
    user_id = int(payload.get("sub", 0))
    svc = QuotationService(session)
    sheet = await svc.create_sheet(body, tenant_id, user_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="投标项目不存在")
    return ApiResponse(data=QuotationSheetOut.model_validate(sheet))


@router.put("/{sheet_id}", response_model=ApiResponse[QuotationSheetOut])
async def update_sheet(
    sheet_id: int,
    body: QuotationSheetUpdate,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """更新报价表"""
    svc = QuotationService(session)
    sheet = await svc.update_sheet(sheet_id, tenant_id, body)
    if not sheet:
        raise HTTPException(status_code=404, detail="报价表不存在")
    return ApiResponse(data=QuotationSheetOut.model_validate(sheet))


@router.delete("/{sheet_id}", response_model=ApiResponse)
async def delete_sheet(
    sheet_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """删除报价表（级联删除明细行）"""
    svc = QuotationService(session)
    ok = await svc.delete_sheet(sheet_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="报价表不存在")
    return ApiResponse(data={"deleted": True})


@router.post("/{sheet_id}/recalculate", response_model=ApiResponse[QuotationSheetOut])
async def recalculate_total(
    sheet_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """重新计算报价表总金额"""
    svc = QuotationService(session)
    sheet = await svc.recalculate_total(sheet_id, tenant_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="报价表不存在")
    return ApiResponse(data=QuotationSheetOut.model_validate(sheet))


# ========== QuotationItem ==========

@router.post("/{sheet_id}/items", response_model=ApiResponse[QuotationItemOut])
async def add_item(
    sheet_id: int,
    body: QuotationItemCreate,
    tenant_id: int = Depends(get_tenant_id),
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """添加报价明细行"""
    user_id = int(payload.get("sub", 0))
    svc = QuotationService(session)
    item = await svc.add_item(sheet_id, tenant_id, body, user_id)
    if not item:
        raise HTTPException(status_code=404, detail="报价表不存在")
    return ApiResponse(data=QuotationItemOut.model_validate(item))


@router.put("/items/{item_id}", response_model=ApiResponse[QuotationItemOut])
async def update_item(
    item_id: int,
    body: QuotationItemUpdate,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """更新报价明细行"""
    svc = QuotationService(session)
    item = await svc.update_item(item_id, tenant_id, body)
    if not item:
        raise HTTPException(status_code=404, detail="报价明细不存在")
    return ApiResponse(data=QuotationItemOut.model_validate(item))


@router.delete("/items/{item_id}", response_model=ApiResponse)
async def delete_item(
    item_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """删除报价明细行"""
    svc = QuotationService(session)
    ok = await svc.delete_item(item_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="报价明细不存在")
    return ApiResponse(data={"deleted": True})
