"""
文档管理 API 路由 — 投标文件列表 + 下载

说明:
  投标文件的导出/下载已由 bid_project.py 中的 /export 和 /download 端点处理。
  本模块仅保留对 storage/bid_outputs/ 目录的通用文件浏览功能，
  供管理员查看所有已导出的投标文件。
"""
import os
import glob
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.deps import get_current_user_payload, get_tenant_id
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/documents", tags=["文档管理"])

# 投标文件输出目录
BID_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "storage", "bid_outputs"
)


@router.get("", response_model=ApiResponse)
async def list_bid_documents(
    payload: dict = Depends(get_current_user_payload),
    tenant_id: int = Depends(get_tenant_id),
):
    """列出已生成的投标文件"""
    os.makedirs(BID_OUTPUT_DIR, exist_ok=True)
    all_files = sorted(glob.glob(os.path.join(BID_OUTPUT_DIR, "*.docx")), reverse=True)

    docs = []
    for f in all_files:
        name = os.path.basename(f)
        size = os.path.getsize(f)
        docs.append({"filename": name, "size": size, "size_kb": round(size / 1024, 1)})
    return ApiResponse(data=docs[:50])


@router.get("/download")
async def download_document(
    filename: str = Query(..., description="文件名"),
    payload: dict = Depends(get_current_user_payload),
    tenant_id: int = Depends(get_tenant_id),
):
    """下载指定文档 — 路径遍历防御"""
    # 路径遍历防御：确保 resolved 路径在 BID_OUTPUT_DIR 内
    filepath = os.path.realpath(os.path.join(BID_OUTPUT_DIR, filename))
    if not filepath.startswith(os.path.realpath(BID_OUTPUT_DIR)):
        raise HTTPException(status_code=400, detail="非法文件路径")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=os.path.basename(filepath),
    )
