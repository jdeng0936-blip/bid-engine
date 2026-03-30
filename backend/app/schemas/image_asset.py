"""
图片资源库 Schema — Pydantic V2

覆盖：ImageAsset CRUD
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ImageAssetCreate(BaseModel):
    """创建图片资源"""
    enterprise_id: int = Field(description="所属企业ID")
    category: str = Field(description="图片分类（见 ImageCategory 枚举）")
    title: str = Field(min_length=1, max_length=200, description="图片标题")
    description: Optional[str] = Field(None, description="图片说明文字")
    file_path: str = Field(description="图片存储路径")
    file_name: Optional[str] = Field(None, max_length=200, description="原始文件名")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    mime_type: Optional[str] = Field(None, max_length=50, description="MIME类型")
    width: Optional[int] = Field(None, description="图片宽度（像素）")
    height: Optional[int] = Field(None, description="图片高度（像素）")
    tags: Optional[str] = Field(None, max_length=500, description="标签（逗号分隔）")
    suggested_chapter: Optional[str] = Field(None, max_length=100, description="建议放置的章节")
    is_default: bool = Field(False, description="是否为该分类的默认图片")
    sort_order: int = Field(0, description="排序号")


class ImageAssetUpdate(BaseModel):
    """更新图片资源"""
    category: Optional[str] = None
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    tags: Optional[str] = Field(None, max_length=500)
    suggested_chapter: Optional[str] = Field(None, max_length=100)
    is_default: Optional[bool] = None
    sort_order: Optional[int] = None


class ImageAssetOut(BaseModel):
    """图片资源输出"""
    id: int
    tenant_id: int
    enterprise_id: int
    category: str
    title: str
    description: Optional[str] = None
    file_path: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    tags: Optional[str] = None
    suggested_chapter: Optional[str] = None
    is_default: bool = False
    sort_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
