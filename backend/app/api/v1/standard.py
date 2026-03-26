"""
标准库 API 路由 — 规范文档 CRUD + 条款树管理 + 文件上传解析

所有接口强制 JWT 认证 + tenant_id 隔离。
"""
import os
import tempfile
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
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


# ========== 文件上传解析 ==========

@router.post("/upload", response_model=ApiResponse)
async def upload_and_parse(
    file: UploadFile = File(..., description="规范文件（.doc/.docx）"),
    doc_type: str = Form("安全规程", description="文档类型"),
    version: str = Form("v1.0", description="版本号"),
    payload: dict = Depends(get_current_user_payload),
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """
    上传规范文件 → 自动提取文本 → 章节切分 → 入库 → 向量化

    支持格式: .doc, .docx, .txt
    """
    # 校验文件类型
    filename = file.filename or "unknown.docx"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".doc", ".docx", ".txt"):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，仅支持 .doc/.docx/.txt"
        )

    # 保存临时文件
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from app.services.document_parser import DocumentParserService

        parser = DocumentParserService(session)

        # 解析并入库
        result = parser.parse_and_ingest(
            file_path=tmp_path,
            filename=filename,
            doc_type=doc_type,
            version=version,
            tenant_id=tenant_id,
            created_by=int(payload["sub"]),
        )
        # parse_and_ingest 是 async 方法
        result = await result

        # 异步向量化（不阻塞响应）
        vectorized = await parser.vectorize_document(result["document_id"])
        result["vectorized_count"] = vectorized

        return ApiResponse(
            message=f"文件解析入库成功，共 {result['clause_count']} 条条款",
            data=result,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ========== 规范文档 ==========

@router.get("", response_model=ApiResponse[PaginatedData[StdDocumentOut]])
@router.get("/documents", response_model=ApiResponse[PaginatedData[StdDocumentOut]], include_in_schema=False)
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
@router.post("/documents", response_model=ApiResponse[StdDocumentOut], include_in_schema=False)
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


@router.get("/documents/{doc_id}", response_model=ApiResponse, include_in_schema=False)
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


@router.put("/documents/{doc_id}", response_model=ApiResponse[StdDocumentOut], include_in_schema=False)
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


@router.delete("/documents/{doc_id}", response_model=ApiResponse, include_in_schema=False)
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
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """更新条款"""
    svc = StandardService(session)
    clause = await svc.update_clause(clause_id, body, tenant_id=tenant_id)
    if not clause:
        raise HTTPException(status_code=404, detail="条款不存在")
    return ApiResponse(data=StdClauseOut.model_validate(clause))


@router.delete("/clauses/{clause_id}", response_model=ApiResponse)
async def delete_clause(
    clause_id: int,
    payload: dict = Depends(get_current_user_payload),
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_async_session),
):
    """删除条款（递归删除子条款）"""
    svc = StandardService(session)
    success = await svc.delete_clause(clause_id, tenant_id=tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="条款不存在")
    return ApiResponse(message="删除成功")
