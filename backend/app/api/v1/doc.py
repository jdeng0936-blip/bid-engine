"""
文档生成 API 路由 — 触发生成 + 文件下载 + 文档列表
"""
import os
import glob
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user_payload, get_tenant_id
from app.schemas.common import ApiResponse
from app.schemas.doc import DocGenerateRequest, DocGenerateResult
from app.services.doc_generator import DocGenerator

router = APIRouter(prefix="/projects", tags=["文档生成"])

# 输出目录
OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "storage", "outputs"
)


@router.post("/{project_id}/generate", response_model=ApiResponse[DocGenerateResult])
async def generate_document(
    project_id: int,
    tenant_id: int = Depends(get_tenant_id),
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """一键生成规程文档（参数→规则匹配→计算校核→Word 输出）"""
    gen = DocGenerator(session)
    try:
        result = await gen.generate(project_id, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(data=result)


@router.get("/{project_id}/documents", response_model=ApiResponse)
async def list_documents(
    project_id: int,
    payload: dict = Depends(get_current_user_payload),
):
    """列出已生成的文档"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.docx")), reverse=True)
    docs = []
    for f in files[:20]:
        name = os.path.basename(f)
        size = os.path.getsize(f)
        docs.append({"filename": name, "size": size, "size_kb": round(size / 1024, 1)})
    return ApiResponse(data=docs)


@router.get("/{project_id}/documents/download")
async def download_document(
    project_id: int,
    filename: str = Query(..., description="文件名"),
    payload: dict = Depends(get_current_user_payload),
):
    """下载指定文档"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath) or ".." in filename:
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )
