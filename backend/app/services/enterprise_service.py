"""
企业管理 Service — Enterprise CRUD

Tenant 隔离：所有查询注入 tenant_id 过滤。
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enterprise import Enterprise
from app.schemas.enterprise import EnterpriseCreate, EnterpriseUpdate


class EnterpriseService:
    """企业 CRUD 服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_enterprises(self, tenant_id: int) -> list[Enterprise]:
        result = await self.session.execute(
            select(Enterprise)
            .where(Enterprise.tenant_id == tenant_id)
            .order_by(Enterprise.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_enterprise(self, enterprise_id: int, tenant_id: int) -> Optional[Enterprise]:
        result = await self.session.execute(
            select(Enterprise)
            .where(Enterprise.id == enterprise_id, Enterprise.tenant_id == tenant_id)
            .options(
                selectinload(Enterprise.credentials),
                selectinload(Enterprise.images),
            )
        )
        return result.scalar_one_or_none()

    async def create_enterprise(
        self, data: EnterpriseCreate, tenant_id: int, user_id: int
    ) -> Enterprise:
        enterprise = Enterprise(
            tenant_id=tenant_id,
            created_by=user_id,
            **data.model_dump(),
        )
        self.session.add(enterprise)
        await self.session.commit()
        await self.session.refresh(enterprise)
        return enterprise

    async def update_enterprise(
        self, enterprise_id: int, tenant_id: int, data: EnterpriseUpdate
    ) -> Optional[Enterprise]:
        enterprise = await self.get_enterprise(enterprise_id, tenant_id)
        if not enterprise:
            return None
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(enterprise, k, v)
        await self.session.commit()
        await self.session.refresh(enterprise)
        return enterprise

    async def delete_enterprise(self, enterprise_id: int, tenant_id: int) -> bool:
        enterprise = await self.get_enterprise(enterprise_id, tenant_id)
        if not enterprise:
            return False
        await self.session.delete(enterprise)
        await self.session.commit()
        return True
