"""
图片资源库 Service — ImageAsset CRUD

Tenant 隔离：所有查询注入 tenant_id 过滤。
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image_asset import ImageAsset
from app.schemas.image_asset import ImageAssetCreate, ImageAssetUpdate


class ImageAssetService:
    """图片资源 CRUD 服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_enterprise(
        self, enterprise_id: int, tenant_id: int,
        category: Optional[str] = None,
    ) -> list[ImageAsset]:
        stmt = (
            select(ImageAsset)
            .where(
                ImageAsset.enterprise_id == enterprise_id,
                ImageAsset.tenant_id == tenant_id,
            )
        )
        if category:
            stmt = stmt.where(ImageAsset.category == category)
        stmt = stmt.order_by(ImageAsset.sort_order, ImageAsset.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_image(self, image_id: int, tenant_id: int) -> Optional[ImageAsset]:
        result = await self.session.execute(
            select(ImageAsset)
            .where(ImageAsset.id == image_id, ImageAsset.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def create_image(
        self, data: ImageAssetCreate, tenant_id: int, user_id: int
    ) -> ImageAsset:
        image = ImageAsset(
            tenant_id=tenant_id,
            created_by=user_id,
            **data.model_dump(),
        )
        self.session.add(image)
        await self.session.commit()
        await self.session.refresh(image)
        return image

    async def update_image(
        self, image_id: int, tenant_id: int, data: ImageAssetUpdate
    ) -> Optional[ImageAsset]:
        image = await self.get_image(image_id, tenant_id)
        if not image:
            return None
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(image, k, v)
        await self.session.commit()
        await self.session.refresh(image)
        return image

    async def delete_image(self, image_id: int, tenant_id: int) -> bool:
        image = await self.get_image(image_id, tenant_id)
        if not image:
            return False
        await self.session.delete(image)
        await self.session.commit()
        return True

    async def get_defaults_by_category(
        self, enterprise_id: int, tenant_id: int
    ) -> list[ImageAsset]:
        """获取每个分类的默认图片（AI生成文档时使用）"""
        result = await self.session.execute(
            select(ImageAsset)
            .where(
                ImageAsset.enterprise_id == enterprise_id,
                ImageAsset.tenant_id == tenant_id,
                ImageAsset.is_default == True,  # noqa: E712
            )
            .order_by(ImageAsset.category)
        )
        return list(result.scalars().all())
