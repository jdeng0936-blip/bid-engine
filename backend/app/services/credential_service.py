"""
资质证书 Service — Credential CRUD + 到期预警

Tenant 隔离：所有查询注入 tenant_id 过滤。
"""
from typing import Optional
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credential import Credential
from app.models.enterprise import Enterprise
from app.schemas.credential import CredentialCreate, CredentialUpdate
from app.core.config import settings


class CredentialService:
    """资质证书 CRUD 服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_enterprise(
        self, enterprise_id: int, tenant_id: int
    ) -> list[Credential]:
        result = await self.session.execute(
            select(Credential)
            .where(
                Credential.enterprise_id == enterprise_id,
                Credential.tenant_id == tenant_id,
            )
            .order_by(Credential.cred_type)
        )
        return list(result.scalars().all())

    async def get_credential(
        self, cred_id: int, tenant_id: int
    ) -> Optional[Credential]:
        result = await self.session.execute(
            select(Credential)
            .where(Credential.id == cred_id, Credential.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def create_credential(
        self, data: CredentialCreate, tenant_id: int, user_id: int
    ) -> Credential:
        cred = Credential(
            tenant_id=tenant_id,
            created_by=user_id,
            **data.model_dump(),
        )
        self.session.add(cred)
        await self.session.commit()
        await self.session.refresh(cred)
        return cred

    async def update_credential(
        self, cred_id: int, tenant_id: int, data: CredentialUpdate
    ) -> Optional[Credential]:
        cred = await self.get_credential(cred_id, tenant_id)
        if not cred:
            return None
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(cred, k, v)
        await self.session.commit()
        await self.session.refresh(cred)
        return cred

    async def delete_credential(self, cred_id: int, tenant_id: int) -> bool:
        cred = await self.get_credential(cred_id, tenant_id)
        if not cred:
            return False
        await self.session.delete(cred)
        await self.session.commit()
        return True

    async def get_expiring_credentials(
        self, tenant_id: int, days: Optional[int] = None
    ) -> list[Credential]:
        """获取即将到期的资质证书"""
        warn_days = days or getattr(settings, "CREDENTIAL_EXPIRY_WARN_DAYS", 90)
        cutoff = (date.today() + timedelta(days=warn_days)).isoformat()
        today_str = date.today().isoformat()

        result = await self.session.execute(
            select(Credential)
            .where(
                Credential.tenant_id == tenant_id,
                Credential.is_permanent == False,  # noqa: E712
                Credential.expiry_date.isnot(None),
                Credential.expiry_date <= cutoff,
                Credential.expiry_date >= today_str,
            )
            .order_by(Credential.expiry_date)
        )
        return list(result.scalars().all())
